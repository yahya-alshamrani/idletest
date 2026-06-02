# idletest

Test idle request timeouts in Kubernetes.

This is a small FastAPI application that waits for a requested number of
seconds before returning a JSON response.

## Endpoint

```text
GET /idle={seconds}
```

`seconds` must be an integer from `0` through `600`.

Examples:

```bash
curl http://localhost:8080/idle=0
curl http://localhost:8080/idle=5
```

Successful response:

```json
{"message":"Waited for 5 seconds"}
```

Invalid values return `400`:

```bash
curl -i http://localhost:8080/idle=-1
curl -i http://localhost:8080/idle=601
```

## Run Locally

Install dependencies and start the application on port `8080`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn idletest_app:app --host 0.0.0.0 --port 8080
```

Then hit the app:

```bash
curl http://localhost:8080/idle=3
```

## Run With a Container

Build and run the image:

```bash
docker build -f Containerfile -t idletest:local .
docker run --rm -p 8080:8080 idletest:local
```

Then hit the app:

```bash
curl http://localhost:8080/idle=3
```

If you use Podman, the same commands work with `podman` instead of `docker`.

## Run in Kubernetes

Apply the deployment, service, and ingress:

```bash
kubectl apply -f idletest-app.yaml
```

To hit the service without using ingress, port-forward the service:

```bash
kubectl port-forward svc/idletest 8080:8080
curl http://localhost:8080/idle=3
```

To hit the ingress, make sure `myapp.local` resolves to your ingress
controller address, then run:

```bash
curl http://myapp.local/idle=3
```

Or call the ingress address directly with the host header:

```bash
curl -H "Host: myapp.local" http://<INGRESS_IP>/idle=3
```

The included ingress sets NGINX proxy timeouts to `10` seconds. For example,
`/idle=5` should complete, while `/idle=11` is useful for testing timeout
behavior through the ingress.
