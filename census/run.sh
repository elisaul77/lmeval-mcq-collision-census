#!/bin/sh
# Uso (desde la raíz del proyecto): sh choque/run.sh prueba|congela|censo|evalua   ·   CHOQUE_SCRIPT=audit_choque1.py sh choque/run.sh
exec docker run --rm --network none -u "$(id -u):$(id -g)" -v "$(pwd)":/w -w /w pchoque:env python choque/${CHOQUE_SCRIPT:-choque1.py} "$@"
