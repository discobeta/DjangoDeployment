from lib.DjangoDeployment import DjangoDeployment

app = DjangoDeployment('config/example-project.json')

print app.build_directories()
print app.build_models()
print app.build_viewsets()
print app.build_serializers()
print app.build_admin()
print app.build_urls()