FROM alpine
RUN apk add --no-cache curl && curl -I https://google.com
