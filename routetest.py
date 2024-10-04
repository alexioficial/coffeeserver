from coffeeserver import ServeCoffee

sc = ServeCoffee(__name__)

@sc.route('/hola', methods = ['POST'])
def hola(request):
    return request.json_data

@sc.route('/')
def index(_):
    # data = [
    #     { 'nombre': 'Alexi' },
    #     { 'nombre': 'Juan' },
    #     { 'nombre': 'Pedro' }
    # ]
    data = [
        'Alexi',
        'Juan',
        'Pedro'
    ]
    return sc.render('index.html', dict(hola = 'Alexi', data = data))