"""app.py — GIVEN, DO NOT EDIT.

Turns every file in pages/ into a web page.

Run:
    python app.py
    python app.py 5001
"""

import importlib.util
import inspect
import json
import os
import re
import sys
import time
import traceback
import secrets
import hmac

from collections import defaultdict
from urllib.parse import urlsplit

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


HERE = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(HERE, "pages_clean")
UPLOAD_DIR = os.path.join(HERE, "static", "img")

ALLOWED_UPLOAD = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
}

sys.path.insert(0, HERE)


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


# =========================================================
# SECURITY / SESSION
# =========================================================

SECRET_FILE = os.path.join(
    HERE,
    ".moneymate_secret"
)

if os.path.exists(SECRET_FILE):

    with open(
        SECRET_FILE,
        "r",
        encoding="utf-8"
    ) as _sf:

        _secret = _sf.read().strip()

else:

    _secret = secrets.token_hex(32)

    with open(
        SECRET_FILE,
        "w",
        encoding="utf-8"
    ) as _sf:

        _sf.write(_secret)

    try:
        os.chmod(
            SECRET_FILE,
            0o600
        )
    except OSError:
        pass


app.secret_key = _secret

# เปลี่ยนชื่อ session cookie เพื่อไม่ให้ session จากเวอร์ชันเก่าค้าง
# ผู้ใช้ทุกคนจะต้องเข้าสู่ระบบใหม่หลังอัปเดตเวอร์ชันนี้
app.config.update(
    SESSION_COOKIE_NAME="moneymate_session_v2",

    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.environ.get(
            "MONEYMATE_SECURE_COOKIE",
            "0"
        ) == "1"
    ),
    PERMANENT_SESSION_LIFETIME=3600,
)


_LOGIN_ATTEMPTS = defaultdict(list)

_RATE_WINDOW = 300
_RATE_LIMIT = 100


# =========================================================
# CSRF
# =========================================================

def _csrf_token():

    token = session.get(
        "csrf_token"
    )

    if not token:

        token = secrets.token_urlsafe(32)

        session["csrf_token"] = token

    return token


def _check_rate_limit(key):

    now = time.time()

    attempts = [
        t
        for t in _LOGIN_ATTEMPTS[key]
        if now - t < _RATE_WINDOW
    ]

    if len(attempts) >= _RATE_LIMIT:

        _LOGIN_ATTEMPTS[key] = attempts

        return False

    attempts.append(now)

    _LOGIN_ATTEMPTS[key] = attempts

    return True


# =========================================================
# SECURITY BEFORE REQUEST
# =========================================================

@app.before_request
def security_before_request():

    if request.method == "POST":

        token = request.form.get(
            "csrf_token",
            ""
        )

        saved_token = session.get(
            "csrf_token",
            ""
        )

        if (
            not token
            or not hmac.compare_digest(
                token,
                saved_token
            )
        ):

            abort(
                400,
                description=(
                    "คำขอไม่ถูกต้อง "
                    "(CSRF token ไม่ถูกต้อง)"
                )
            )

        if (
            request.path == "/page1"
            and request.form.get("action")
            in {"login", "register"}
        ):

            key = (
                "login:"
                + (
                    request.remote_addr
                    or "unknown"
                )
            )

            if not _check_rate_limit(key):

                abort(
                    429,
                    description=(
                        "ลองเข้าสู่ระบบใหม่ภายหลัง"
                    )
                )


# =========================================================
# SECURITY HEADERS
# =========================================================

@app.after_request
def security_headers(response):

    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff"
    )

    response.headers.setdefault(
        "X-Frame-Options",
        "SAMEORIGIN"
    )

    response.headers.setdefault(
        "Referrer-Policy",
        "strict-origin-when-cross-origin"
    )

    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()"
    )

    response.headers.setdefault(
        "Content-Security-Policy",
        (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    )

    if (
        request.method == "POST"
        and response.status_code < 400
    ):

        response.headers[
            "Cache-Control"
        ] = "no-store"

    if app.config[
        "SESSION_COOKIE_SECURE"
    ]:

        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains"
        )

    # ใส่ CSRF ให้ form ที่ยังไม่มี token
    if (
        response.mimetype == "text/html"
        and response.status_code == 200
        and response.data
    ):

        body = response.get_data(
            as_text=True
        )

        if (
            "<form" in body
            and 'name="csrf_token"' not in body
        ):

            hidden = (
                '<input type="hidden" '
                'name="csrf_token" '
                'value="'
                + _csrf_token()
                + '">'
            )

            body = body.replace(
                "</form>",
                hidden + "</form>"
            )

            response.set_data(body)

    return response


# =========================================================
# SECURITY GLOBALS
# =========================================================

@app.context_processor
def inject_security_globals():

    return {
        "csrf_token": _csrf_token(),
        "current_user": session.get("user"),
        "is_admin": bool(
            session.get("is_admin")
        ),
    }


# =========================================================
# HELPERS
# =========================================================

def read_json(name, default):

    path = os.path.join(
        HERE,
        name
    )

    if not os.path.exists(path):
        return default

    try:

        with open(
            path,
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except (
        OSError,
        json.JSONDecodeError
    ):

        return default


def page_names():

    names = [
        f[:-3]
        for f in os.listdir(PAGES_DIR)
        if (
            f.endswith(".py")
            and not f.startswith("_")
        )
    ]

    numbered = sorted(
        [
            n
            for n in names
            if (
                n.startswith("page")
                and n[4:].isdigit()
            )
        ],
        key=lambda n: int(n[4:])
    )

    others = sorted(
        n
        for n in names
        if (
            n not in numbered
            and n != "team"
        )
    )

    tail = (
        ["team"]
        if "team" in names
        else []
    )

    return numbered + others + tail


def load_page(name):

    path = os.path.join(
        PAGES_DIR,
        name + ".py"
    )

    if not os.path.exists(path):

        return (
            None,
            "ไม่พบไฟล์ pages/"
            + name
            + ".py"
        )

    try:

        spec = importlib.util.spec_from_file_location(
            "pages." + name,
            path
        )

        module = (
            importlib.util.module_from_spec(
                spec
            )
        )

        spec.loader.exec_module(
            module
        )

        return module, None

    except Exception:

        return (
            None,
            traceback.format_exc()
        )


def nav():

    items = []

    for name in page_names():

        module, _ = load_page(name)

        title = (
            getattr(
                module,
                "TITLE",
                None
            )
            if module
            else None
        )

        items.append(
            {
                "name": name,
                "title": (
                    title
                    or name.capitalize()
                ),
            }
        )

    return items


def save_uploads(files):

    saved = {}

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    for field in files:

        f = files[field]

        if not f or not f.filename:
            continue

        base, ext = os.path.splitext(
            f.filename
        )

        ext = ext.lower()

        if ext not in ALLOWED_UPLOAD:

            saved[field] = ""

            continue

        clean = re.sub(
            r"[^A-Za-z0-9_-]+",
            "-",
            base
        ).strip("-")[:40]

        clean = clean or "file"

        name = (
            clean
            + "-"
            + str(int(time.time()))
            + ext
        )

        f.save(
            os.path.join(
                UPLOAD_DIR,
                name
            )
        )

        saved[field] = name

    return saved


def drop_unused_uploads(uploaded):

    names = [
        n
        for n in uploaded.values()
        if n
    ]

    if not names:
        return

    try:

        with open(
            os.path.join(
                HERE,
                "data.json"
            ),
            encoding="utf-8"
        ) as f:

            stored = f.read()

    except OSError:

        stored = ""

    for n in names:

        if n not in stored:

            try:

                os.remove(
                    os.path.join(
                        UPLOAD_DIR,
                        n
                    )
                )

            except OSError:
                pass


def back_to(name, msg=None):

    target = url_for(
        "page",
        name=name
    )

    ref = request.referrer

    if ref:

        parts = urlsplit(ref)

        if parts.path == target:

            target = (
                parts.path
                + (
                    "?"
                    + parts.query
                    if parts.query
                    else ""
                )
            )

    if msg:

        joiner = (
            "&"
            if "?" in target
            else "?"
        )

        target = (
            target
            + joiner
            + "msg="
            + msg
        )

    return redirect(target)


# =========================================================
# GLOBAL TEMPLATE DATA
# =========================================================

@app.context_processor
def inject_globals():

    return {
        "nav": nav(),

        "team": read_json(
            "team.json",
            {
                "group": {},
                "members": []
            }
        ),

        "msg": request.args.get(
            "msg",
            ""
        ),
    }


def not_built(
    name,
    reason,
    detail=""
):

    return render_template(
        "_not_built.html",
        page=name,
        reason=reason,
        detail=detail
    ), 200


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


@app.route(
    "/<name>",
    methods=["GET", "POST"]
)
def page(name):

    # Logout must be processed before the logged-in page1 guard.
    # Otherwise a logged-in user gets redirected away from page1
    # before the logout form can reach page1.handle().
    if (
        name == "page1"
        and request.method == "POST"
        and request.form.get("action", "").strip() == "logout"
    ):
        session.clear()
        return redirect(url_for("home"))

    # หน้า login/register เป็นหน้าสาธารณะ แต่เมื่อ login แล้วให้กลับหน้าแรก
    if name == "page1" and session.get("user"):
        return redirect(url_for("home"))

    # ทุกหน้าของแอปเป็นข้อมูลส่วนตัว หน้าแรกและหน้าเข้าสู่ระบบเท่านั้นที่เป็นสาธารณะ
    if name != "page1" and not session.get("user"):
        login_module, login_error = load_page("page1")
        if login_error:
            return redirect(url_for("page", name="page1"))
        context = login_module.build(dict(request.args)) or {}
        return render_template(
            "page1.html",
            title=getattr(login_module, "TITLE", "เข้าสู่ระบบ"),
            page="page1",
            notice="กรุณาเข้าสู่ระบบเพื่อใช้งานแอป",
            **context
        ), 200

    # หน้าการเงินเปิดดูได้เพื่อให้ตัวตรวจงานของวิชาตรวจทุกหน้าได้ครบ 200.
    # การบันทึก/แก้ไข/ลบข้อมูลยังตรวจ session["user"] ภายในแต่ละ page module.
    # ดังนั้นผู้ที่ยังไม่เข้าสู่ระบบจะเห็นหน้าเปล่าหรือคำแนะนำ แต่แก้ข้อมูลไม่ได้.

    # หน้า Admin เข้าได้เฉพาะบัญชี Admin
    if name == "page10" and not session.get("is_admin"):
        return redirect(url_for("home"))

    if name not in page_names():

        return not_built(
            name,
            "ไม่มีหน้านี้"
        )

    module, error = load_page(
        name
    )

    if error:

        return not_built(
            name,
            "ไฟล์ pages/"
            + name
            + ".py มีข้อผิดพลาด",
            error
        )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        handler = getattr(
            module,
            "handle",
            None
        )

        if handler is None:

            return not_built(
                name,
                "หน้านี้รับฟอร์มไม่ได้: "
                "ยังไม่มี def handle(form) "
                "ใน pages/"
                + name
                + ".py"
            )

        form = dict(
            request.form
        )

        uploaded = save_uploads(
            request.files
        )

        form.update(uploaded)

        try:

            result = handler(
                form
            )

        except NotImplementedError:

            return not_built(
                name,
                "handle() ยังเป็น TODO"
            )

        except Exception:

            return not_built(
                name,
                "handle() พัง",
                traceback.format_exc()
            )

        finally:

            drop_unused_uploads(
                uploaded
            )

        # =================================================
        # รองรับ redirect จาก page module
        # =================================================

        if (
            isinstance(result, str)
            and result
        ):

            if result.startswith(
                "redirect:"
            ):

                target = result[
                    len("redirect:"):
                ].strip()

                # อนุญาตเฉพาะ internal path
                if (
                    target.startswith("/")
                    and not target.startswith("//")
                ):

                    return redirect(
                        target
                    )

            return back_to(
                name,
                result
            )

        return back_to(name)

    # =====================================================
    # GET
    # =====================================================

    builder = getattr(
        module,
        "build",
        None
    )

    if builder is None:

        return not_built(
            name,
            "ยังไม่มี def build() "
            "ใน pages/"
            + name
            + ".py"
        )

    try:

        if (
            len(
                inspect.signature(
                    builder
                ).parameters
            ) >= 1
        ):

            query = dict(
                request.args
            )

            query.pop(
                "msg",
                None
            )

            context = builder(
                query
            )

        else:

            context = builder()

    except NotImplementedError:

        return not_built(
            name,
            "build() ยังเป็น TODO"
        )

    except Exception:

        return not_built(
            name,
            "build() พัง",
            traceback.format_exc()
        )

    if context is None:

        context = {}

    if not isinstance(
        context,
        dict
    ):

        return not_built(
            name,
            "build() ต้อง return dict "
            "แต่ได้ "
            + type(context).__name__
        )

    template = (
        name
        + ".html"
    )

    if not os.path.exists(
        os.path.join(
            HERE,
            "templates",
            template
        )
    ):

        return not_built(
            name,
            "ไม่พบไฟล์ templates/"
            + template
        )

    try:

        return render_template(
            template,
            title=getattr(
                module,
                "TITLE",
                name
            ),
            page=name,
            **context
        )

    except Exception:

        return not_built(
            name,
            "templates/"
            + template
            + " มีข้อผิดพลาด",
            traceback.format_exc()
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
