# Matrix Dynamics Explorer

A web app for exploring how polynomials behave when you iterate them — feed the output back in
as the next input, over and over, and watch whether the sequence settles down or runs away.

Built for the Loyola University Maryland mathematics department as a senior capstone project by
Kevin Murray and a project partner.

## What it does

You give it a polynomial such as `2x^2 - 1`, a starting value, an iteration cap, and a
convergence threshold. It then applies the polynomial repeatedly and reports what happens.

The starting value can be any of three things:

- **A number** — classic one-dimensional iteration. The app tracks the difference between
  successive values and graphs how quickly it settles.
- **A matrix** (up to 5×5) — the polynomial is evaluated as a true matrix polynomial, so the
  constant term is `c·I` rather than an elementwise add. It graphs the matrix norm and the
  eigenvalues at each step.
- **A CSV of matrices** — batch mode. Each row is one flattened square matrix, and every row is
  iterated independently so you can compare behaviour across many starting points at once.

A run stops when successive values differ by less than the threshold (converged) or when the
iteration cap is reached. Results are graphed in the browser and can be exported back to CSV.

## How it works

The interesting part is the polynomial parser, which is written from scratch rather than
delegating to `eval` or a symbolic library.

```
"2x^2 - 1"
   │
   ├─ cleanPoly      normalise: strip spaces, insert implicit multiplication
   │                 ("5x" -> "5*x"), rewrite unary minus ("-x" -> "-1*x")
   ├─ verifyPoly     reject malformed input before it reaches the parser
   └─ parsePoly      recursive descent into a binary expression tree
                       │
                     AdditionNode / SubtractionNode
                     MultiplicationNode / DivisionNode
                     ExponentNode
                     VariableNode / ConstantNode
```

Each node knows how to evaluate itself against a value, so the same tree works for scalars and
for numpy matrices — the nodes branch on type and promote scalars to `c·I` where the operand is
a matrix. Operator precedence falls out of the tree's shape rather than needing a separate pass.

Long runs execute in a background thread while the browser polls for progress, so a slow
computation does not block the response.

```
main/controller/parseTree/   parser, node types, iteration driver, matrix and CSV I/O
main/controller/             database-facing helpers for iteration records
main/views.py                HTTP endpoints
main/templates/              UI and the polling/graphing frontend
main/tests.py                46 tests, mostly parser and iteration behaviour
```

## Running it locally

Requires Python 3.11 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
```

Set `DJANGO_DEBUG=True` in `.env` for local work — a throwaway secret key is then generated
automatically, so no further configuration is needed.

```bash
.venv/bin/python manage.py migrate
DJANGO_DEBUG=True .venv/bin/python manage.py runserver
```

Then open http://localhost:8000.

Run the test suite:

```bash
DJANGO_DEBUG=True .venv/bin/python manage.py test
```

## Deploying

The app reads all environment-specific configuration from environment variables and serves its
own static files through WhiteNoise, so it runs on any host that can start a WSGI process.

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | **Required** when `DJANGO_DEBUG` is false; the app refuses to start without it |
| `DJANGO_DEBUG` | `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames, e.g. `example.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins with scheme, e.g. `https://example.com` |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` only if your host does not already force HTTPS |

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn mde.wsgi:application
```

Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## Notes

The default database is SQLite, which is fine for a single instance but does not survive the
ephemeral filesystems most platforms-as-a-service use. Point `DATABASES` at Postgres if runs need
to persist across deploys.

Iteration work currently runs in a thread inside the web process. That is adequate for modest
workloads but has no retry or cross-process visibility; a task queue would be the next step.
