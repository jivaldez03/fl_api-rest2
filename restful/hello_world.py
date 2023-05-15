from flask_restful import Resource

class HelloWorld(Resource):
    def get(self):
        return {'hola': 'hello world'}
    
    

