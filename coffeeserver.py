import urllib.parse
import http.server
import json
import os
import datetime
from bs4 import BeautifulSoup

def _render(html: str, context: dict):
    soup = BeautifulSoup(html, 'html.parser')

    # Reemplazo de variables con cf_var
    for var_tag in soup.find_all('cf_var'):
        variable_expression = var_tag.get_text()
        try:
            var_tag.replace_with(str(eval(variable_expression, {}, context)))
        except Exception:
            var_tag.replace_with('')

    # Reemplazo de bucles con cf_for
    for for_tag in soup.find_all('cf_for'):
        iterator_name = for_tag.get('iterator')
        iterable_name = for_tag.get('in')

        if iterable_name in context:
            iterable = context[iterable_name]
            new_content = []
            original_html = for_tag.decode_contents()

            for item in iterable:
                local_context = {**context, iterator_name: item}
                fragment = BeautifulSoup(original_html, 'html.parser')

                for inner_var_tag in fragment.find_all('cf_for_var'):
                    variable_expression = inner_var_tag.get_text()
                    try:
                        inner_var_value = str(eval(variable_expression, {}, local_context))
                        inner_var_tag.replace_with(inner_var_value)
                    except Exception:
                        inner_var_tag.replace_with('')
                new_content.append(fragment.decode_contents())
            for_tag.replace_with(BeautifulSoup('\n'.join(new_content), 'html.parser'))
    
    # Reemplazo para las condiciones:
    for cond_tag in soup.find_all('cf_cond'):
        main_condition = cond_tag.find('cf_if')
        elifs = cond_tag.find_all('cf_elif')
        else_condition = cond_tag.find('cf_else')
        
        main_condition_condition = main_condition.attrs
        print(elifs.attrs)

    return str(soup)

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, _, *args):
        client_ip = self.client_address[0]
        status_code = int(args[1])

        RED = "\033[91m"
        ORANGE = "\033[38;5;214m" # ANSI extendido para naranja
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        INDIGO = "\033[38;5;54m"  # ANSI extendido para índigo
        VIOLET = "\033[95m"
        RESET = "\033[0m"

        if 200 <= status_code < 300:
            color = GREEN
        elif 300 <= status_code < 400:
            color = BLUE
        elif 400 <= status_code < 600:
            color = RED
        else:
            color = RESET

        fechaahora_format = datetime.datetime.now().strftime("%d/%b/%Y %H:%M:%S")
        http_version = self.request_version

        custom_log = f"{color}{status_code}{RESET} | {YELLOW}{client_ip}{RESET} - [{ORANGE}{fechaahora_format}{RESET}] \"{self.command} {VIOLET}{self.path}{RESET} {http_version}\""
        print(custom_log)

    
    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def handle_request(self, http_method):
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path.startswith('/static/'):
            self.serve_static_file(parsed_path.path)
            return

        if parsed_path.path in Coffee.routes:
            if http_method in Coffee.routes[parsed_path.path]:
                handler = Coffee.routes[parsed_path.path][http_method]
                request_instance = Request(self)
                response = handler(request_instance)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                if isinstance(response, dict):  # Verificar si la respuesta es un diccionario
                    response = json.dumps(response)  # Convertir a JSON

                self.wfile.write(response.encode())
            else:
                self.send_response(405)  # Method Not Allowed
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Method not allowed</h1></body></html>')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Page not found</h1></body></html>')
    
    def serve_static_file(self, file_path):
        file_path = file_path.lstrip('/static/')
        full_file_path = os.path.join('static', file_path)

        if os.path.exists(full_file_path) and os.path.isfile(full_file_path):
            with open(full_file_path, 'rb') as file:
                content = file.read()

            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>File not found</h1></body></html>')

class Request:
    def __init__(self, http_handler):
        self.method = http_handler.command
        self.headers = http_handler.headers
        self.path = http_handler.path
        self.body = None

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            self.body = http_handler.rfile.read(content_length)
            try:
                self.json_data = json.loads(self.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.json_data = {}

class ServeCoffee:
    def __init__(self, name, template_folder = 'templates', url_prefix = ''):
        self.name = name
        self.template_folder = template_folder
        self.url_prefix = url_prefix
        self.routes = {}

    def route(self, path, methods = ['GET']):
        def decorator(handler_func):
            for method in methods:
                self.routes[method] = (self.url_prefix + path, handler_func)
            return handler_func
        return decorator

    def render(self, file_name, context: dict):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, str(self.template_folder))
        template = open(os.path.join(template_dir, file_name), 'r').read()

        rendered_template = _render(template, context)
        return rendered_template

class Coffee:
    routes = {}
    def __init__(self, name, template_folder = 'templates'):
        self.name = name
        self.template_folder = template_folder

    def drink(self, host = 'localhost', port = 5000):
        server = http.server.HTTPServer((host, port), RequestHandler)
        print(f'Server running on http://{host}:{port}')
        server.serve_forever()

    def render(self, file_name, context: dict):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, str(self.template_folder))
        template = open(os.path.join(template_dir, file_name), 'r').read()

        rendered_template = _render(template, context)
        return rendered_template

    @classmethod
    def route(cls, path, methods = ['GET']):
        def decorator(handler_func):
            if path not in cls.routes:
                cls.routes[path] = {}
            for method in methods:
                cls.routes[path][method] = handler_func
            return handler_func
        return decorator
    
    def serve_coffee(self, serve_coffee_instance):
        for method, (path, handler_func) in serve_coffee_instance.routes.items():
            if path not in self.routes:
                self.routes[path] = {}
            self.routes[path][method] = handler_func