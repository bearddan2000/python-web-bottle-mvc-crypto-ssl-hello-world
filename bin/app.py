from bottle import (
    route,
    response,
    run,
    redirect,
    request,
    static_file,
    ServerAdapter,
    default_app,
)
from beaker.middleware import SessionMiddleware
import crypt
import spwd
import pwd

@route("/<filename:path>")
def send_static(filename):
    session = beaker_session()
    username = session.get("username", None)
    print(filename)
    if filename == 'protected.html' and username is None:
        return redirect('/index.html')
    return static_file(filename, root="./templates")

@route("/whoami")
def whoami():
    try:
        username = current_user()
    except:
        username = None
    finally:
        response.set_header("Cache-Control", "no-cache")
        return {"d": username}


@route("/")
def default():
    redirect("/index.html")


@route("/login", method="POST")
def login():
    name = request.forms.username
    passwd = request.forms.password

    if name == 'user' and passwd == 'pass':
        session = beaker_session()
        session["username"] = name
        redirect("/protected.html")
    else:
        redirect("/index.html")


@route("/logout", method="POST")
def logout():
    session = beaker_session()
    session.delete()
    redirect("/index.html")


def beaker_session():
    return request.environ.get("beaker.session")


def current_user():
    session = beaker_session()
    username = session.get("username", None)
    if username is None:
        raise Exception("Unauthenticated user")
    return username


class SSLCherootAdapter(ServerAdapter):
    def run(self, handler):
        from cheroot import wsgi
        from cheroot.ssl.builtin import BuiltinSSLAdapter
        import ssl

        server = wsgi.Server((self.host, self.port), handler)
        server.ssl_adapter = BuiltinSSLAdapter("cert/server.crt", "cert/server.key")

        try:
            server.start()
        finally:
            server.stop()


# define beaker options
# -Each session data is stored inside a file located inside a
#  folder called data that is relative to the working directory
# -The cookie expires at the end of the browser session
# -The session will save itself when accessed during a request
#  so save() method doesn't need to be called
session_opts = {
    "session.type": "file",
    "session.cookie_expires": True,
    "session.data_dir": "./data",
    "session.auto": True,
}

# Create the default bottle app and then wrap it around
# a beaker middleware and send it back to bottle to run
app = SessionMiddleware(default_app(), session_opts)

if __name__ == "__main__":
    run(app=app, host="0.0.0.0", port=443, server=SSLCherootAdapter)
