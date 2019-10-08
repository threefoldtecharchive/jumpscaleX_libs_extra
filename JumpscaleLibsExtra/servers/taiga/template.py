def nginx_conf():
    return """
    server {
        listen %(port)s default_server;
        server_name _;

        large_client_header_buffers 4 32k;
        client_max_body_size 50M;
        charset utf-8;

        access_log %(log_dir)s/nginx.access.log;
        error_log %(log_dir)s/nginx.error.log;

        # Frontend
        location / {
            root %(front_end)s/dist/;
            try_files $uri $uri/ /index.html;
        }

        # Backend
        location /api {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_pass http://127.0.0.1:8001/api;
            proxy_redirect off;
        }

        # Admin access (/admin/)
        location /admin {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_pass http://127.0.0.1:8001$request_uri;
            proxy_redirect off;
        }

        # Static files
        location /static {
            alias %(back_end)s/static;
        }

        # Media files
        location /media {
            alias %(back_end)s/media;
        }

        # Events
        location /events {
            proxy_pass http://127.0.0.1:8888/events;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_connect_timeout 7d;
            proxy_send_timeout 7d;
            proxy_read_timeout 7d;
        }
    }
"""
