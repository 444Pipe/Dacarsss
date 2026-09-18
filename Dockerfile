# DACARS — sitio estático servido con Caddy.
# No hay compilación: el contenido se copia tal cual.
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY . /srv

# El Caddyfile y el Dockerfile van en el contexto de build pero no se publican.
# Si el Caddyfile tiene un error de sintaxis, el build falla acá y no en producción.
RUN rm -f /srv/Caddyfile /srv/Dockerfile \
 && caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

# Railway sobreescribe PORT; 8080 es solo el valor por defecto en local.
ENV PORT=8080
EXPOSE 8080

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
