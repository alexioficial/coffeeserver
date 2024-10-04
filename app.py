from coffeeserver import Coffee

coffee = Coffee(__name__)

from routetest import sc as routetest

coffee.serve_coffee(routetest)

if __name__ == '__main__':
    coffee.drink('0.0.0.0', 7100)