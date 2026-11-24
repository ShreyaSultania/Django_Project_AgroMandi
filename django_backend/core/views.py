from django.http import HttpResponse

def root_view(request):
    """
    Matches GET / in Express server.js:
    app.get("/", (req, res) => { res.send("Agro AI System API is running"); });
    """
    return HttpResponse("Agro AI System API is running", content_type="text/plain")

def socket_io_handler(request):
    """
    Handles socket.io polling requests from frontend socket.js gracefully
    so the browser console does not throw 404 errors.
    """
    # Engine.IO v4 handshake response format
    payload = '0{"sid":"agro_ai_session","upgrades":[],"pingInterval":25000,"pingTimeout":20000}'
    response = HttpResponse(payload, content_type="text/plain; charset=UTF-8")
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Credentials"] = "true"
    return response
