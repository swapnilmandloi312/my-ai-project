# Work Relay quickstart
From repository root, Python 3.11+:
```sh
python -m swapnil_ai_labs.relay_demo
python -m unittest -v swapnil_ai_labs.test_relay_client swapnil_ai_labs.test_work_relay swapnil_ai_labs.test_relay_http
```
Or install the source package with `pip install .` inside a virtual environment; run `swapnil-ai-labs-relay`. The demo makes actual authenticated HTTP calls on loopback, with temporary SQLite storage and randomly generated ephemeral credentials, for four synthetic departments. Each demonstrates missing evidence and unapproved resolution denial, then reviewer approval and operator resolution, restart persistence and local audit verification. No external changes, customer data or model inference.
```sh
docker build -f deployment/relay.Dockerfile -t relay-candidate .
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cap-drop ALL --security-opt no-new-privileges relay-candidate python -m swapnil_ai_labs.relay_demo
```
The Docker image includes a Gunicorn entrypoint for a future configured service. The demo validates only loopback execution inside an isolated container, not a hosted multi-worker production deployment. Follow WORK_RELAY.md for configuration, limits and required release gates. The Python RelayClient requires HTTPS for non-loopback origins, rejects redirects, bounds response bytes, and does not retry automatically. It has a socket timeout, not a complete end-to-end deadline. Do not embed bearer tokens in a browser or expose the WSGI service directly. Preserve the existing Netlify website.
