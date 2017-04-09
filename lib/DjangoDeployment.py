import json, os
from argparse import Namespace

class DjangoDeployment:
    """
    Django Deployment Class. 
    
    Currently supports the creation of Models, Methods, Serializers and Viewsets. 
    
    The following Model fields are supported:
    
    CharField
    EmailField
    BooleanField
    DateTimeField
    IntegerField
    FilePathField

    And the following relationships:

    one_to_one
    many_to_many
    """
    DEFAULTS = {
        "CharField": "(max_length=500, blank=True, null=True)",
        "EmailField": "()",
        "BooleanField": "(default=False)",
        "DateTimeField": "(null=True, blank=True)",
        "IntegerField": "(default=0, blank=True, null=True)",
        "ImageField": "(upload_to='default/static/u/')"}

    MAPPING = {
        "EmailField": ['email'],
        "BooleanField": ['_flag', 'show_', 'hide_', 'status'],
        "DateTimeField": ['_on', '_period'],
        "IntegerField": ['_count', '_id'],
        "ImageField": ['_logo', 'image', 'picture', '_file']}

    def __init__(self, configuration_file):
        """
        Loads the configuration upon initialization.
        :param configuration_file:
        """
        self.configuration_file = configuration_file
        self.load_configuration()

    def build_directories(self):
        """
        Creates the requires directories
        :return:
        """
        if not os.path.exists(self.config.name):
            os.makedirs(self.config.name)
            with open(self.config.name + '/__init__.py', 'a'):
                os.utime(self.config.name + '/__init__.py', None)

        for dir in [self.config.name+'/migrations',
                    self.config.name+'/models',
                    self.config.name+'/viewsets',
                    self.config.name+'/serializers',
                    self.config.name+'/management',
                    self.config.name + '/management/commands',
                    ]:
            if not os.path.exists(dir):
                os.makedirs(dir)
                with open(dir+'/__init__.py', 'a'):
                    os.utime(dir+'/__init__.py', None)

    def build_models(self):
        """
        Build the Model definitions
        :return:
        """
        for model in self.config.models:
            self.imports = "# models\n\n"
            self.imports += "from django.db import models\n"
            self.imports += "from django.contrib.auth.models import User\n"
            self.imports += "from datetime import datetime\n"
            self.model = "\n\n" + "class " + model.name.title() + "(models.Model):" + "\n"
            # Add fields
            self.model += "\n\t# fields\n"
            for field in model.fields:
               self.model += "\t" + field + " = models." + self.determine_field_type(field) + app.DEFAULTS[self.determine_field_type(field)] + "\n"

            # Add OneToMany
            self.model += "\n\t# relationships\n"
            for field in model.one_to_one:
                self.imports += "from " + self.config.name + ".models." + field + " import " + field.title() + "\n"
                self.model += "\t" + field + " = models.OneToOneField(" + field.title() + ", null=True)\n"

            # optional user owner field
            if app.config.add_user_field:
                self.model += "\tuser = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name=\""+model.name+"s\")\n"

            # Add ManyToMany
            for field in model.many_to_many:
                self.imports += "from " + self.config.name + ".models." + field + " import " + field.title() + "\n"
                self.model += "\t" + field + " = models.ManyToManyField(" + field.title() + ", blank=True, null=True)\n"

            # Add optional meta fields
            self.model += "\n"
            if app.config.add_created_on_field:
                self.model += "\tcreated_on = models.DateTimeField(default=datetime.now, blank=True)\n"
                if app.config.add_updated_on_field:
                    self.model += "\tupdated_on = models.DateTimeField(auto_now=True, null=True)\n"

            # Add methods
            self.model += "\n\t# methods\n"
            for method in model.methods:
                self.model += "\tdef " + method + "(self):\n\t\tpass\n"
            
            #self.model += "\tdef save(self, *args, **kwargs):\n"
            #self.model += "\t\tsuper(" + self.config.name.title() + ", self).save(*args, **kwargs)\n"

            # Add meta methods
            self.model += "\tdef __unicode__(self):\n";
            self.model += "\t\treturn unicode(self." + model.fields[0] + ")\n"
            # Add class meta
            self.model += "\n"
            self.model += "\tclass Meta:\n"
            self.model += "\t\tdb_table = '" + model.name + "'\n"
            self.model += "\t\tordering = ('" + model.fields[0] + "',)\n"

            self.write_file(self.imports+self.model,self.config.name+'/models/'+model.name+'.py')

    def build_serializers(self):
        """
        Build the Serializers definitions
        :return:
        """
        for model in self.config.models:
            self.serializer = "# serializers\n\n"
            self.serializer += "from " + self.config.name + ".models." + model.name + " import " + model.name.title() + "\n"
            self.serializer += "from rest_framework import serializers\n"
            self.serializer += "\n\n" + "class " + model.name.title() + "Serializer(serializers.HyperlinkedModelSerializer):" + "\n"

            # Add class meta
            self.serializer += "\tclass Meta:\n"
            self.serializer += "\t\tmodel = " + model.name.title() + "\n"
            self.serializer += "\t\tfields = (\n"
            for field in model.fields:
                self.serializer += "\t\t'" + field + "',\n"
            self.serializer += "\t\t'user',\n"
            if app.config.add_updated_on_field:
                self.serializer += "\t\t'updated_on',\n"
            if app.config.add_created_on_field:
                self.serializer += "\t\t'created_on',\n"
            self.serializer += "\t)\n"
            self.serializer += "\tuser = serializers.ReadOnlyField(source='user.username')\n"

            self.write_file(self.serializer,self.config.name+'/serializers/'+model.name+'.py')

    def build_viewsets(self):
        """
        Build the Viewsets definitions
        :return:
        """
        for model in self.config.models:

            self.viewset = "# viewsets\n\n"
            self.viewset += "from rest_framework import viewsets\n"
            self.viewset += "from rest_framework import permissions\n"
            self.viewset += "from rest_framework.authentication import SessionAuthentication, TokenAuthentication\n"
            self.viewset += "from rest_framework.response import Response\n"
            self.viewset += "from rest_framework.permissions import IsAuthenticated\n\n"

            self.viewset += "from " + self.config.name + ".serializers." + model.name + " import " + model.name.title() + "Serializer\n"
            self.viewset += "from " + self.config.name + ".models." + model.name + " import " + model.name.title() + "\n"
            self.viewset += "\n\n" + "class " + model.name.title() + "ViewSet(viewsets.ModelViewSet):" + "\n"

            # Add class meta
            self.viewset += "\n"
            self.viewset += "\tqueryset = " + model.name.title() + ".objects.all()\n"
            self.viewset += "\tserializer_class = " + model.name.title() + "Serializer\n"
            self.viewset += "\tauthentication_classes = (SessionAuthentication, TokenAuthentication)\n"
            self.viewset += "\tpermission_classes = (IsAuthenticated,)\n"

            if app.config.add_user_field:
                self.viewset += "\tdef get_queryset(self):\n"
                self.viewset += "\t\tqueryset = " + model.name.title() + ".objects.filter(user=self.request.user).order_by('-id')\n"
                self.viewset += "\t\treturn queryset\n"

    
            # permissions
            self.viewset += "\tdef perform_create(self, serializer):\n"
            self.viewset += "\t\tserializer.save(user=self.request.user)\n"

            self.write_file(self.viewset,self.config.name+'/viewsets/'+model.name+'.py')

    def build_admin(self):
        """
        Builds and writes the admin definitions.
        :return:
        """
        self.admin = "# admin\n"
        self.admin = "from django.contrib import admin\n"
        for model in self.config.models:
            self.admin += "from "+self.config.name+".models."+model.name+" import "+model.name.title()+"\n"
        for model in self.config.models:
            self.admin += "admin.site.register(" + model.name.title() + ")\n"
        self.write_file(self.admin,self.config.name+"/admin.py")

    def build_urls(self):
        """
        Creates the requires directories
        :return:
        """
        self.urls = "# urls\n\nfrom rest_framework import routers\n"
        for model in self.config.models:
            self.urls += "from " + self.config.name + ".viewsets." + model.name + " import " + model.name.title() + "ViewSet\n"
        for model in self.config.models:
            self.urls += "from " + self.config.name + ".models." + model.name + " import " + model.name.title() + "\n\n"
        self.urls += "def " + self.config.name + "_api_routes_v1():\n"
        self.urls += "\trouter = routers.DefaultRouter()\n"
        for model in self.config.models:
            self.urls += "\trouter.register(r'" + model.name + "', " + model.name.title() + "ViewSet)\n"
        self.urls += "\treturn router\n"

        f = open(self.config.name+'/urls.py', 'w+')
        f.write(self.urls)

    def write_file(self,content,filename):
        """
        Overwrites a file.
        :param content:
        :param filename:
        :return:
        """
        f = open(filename, 'w+')
        f.write(content)
        f.close()

    def load_configuration(self):
        """
        Converts JSON configuration file into our object.config
        :return:
        """
        self.config = json.loads(open(self.configuration_file).read(), object_hook=lambda d: Namespace(**d))

    def determine_field_type(self, field_name):
        """
        Determines the type of Model.X field to use
        Configure field mapping with self.MAPPING
        CharField is default
        :param field_name:
        :return:
        """
        for type in self.MAPPING:
            for map in self.MAPPING[type]:
                if map in field_name:
                    return type

        return "CharField"

    def __unicode__(self):
        return self.name
