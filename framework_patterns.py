"""
Framework Detection Patterns

This module contains patterns for detecting various frameworks and project types.
It's used by the ProjectAnalyzer to identify what frameworks are being used in a project.
"""

# Web Frameworks
WEB_FRAMEWORKS = {
    'django': {
        'files': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py', 'asgi.py'],
        'imports': ['django'],
        'content_patterns': ['DJANGO_SETTINGS_MODULE', 'django.db.models', 'django.urls'],
        'weight': 0.8
    },
    'flask': {
        'files': ['app.py', 'wsgi.py', 'application.py'],
        'imports': ['flask', 'Flask'],
        'content_patterns': ['from flask import', 'import flask', 'Flask(__name__)', '@app.route'],
        'weight': 0.7
    },
    'fastapi': {
        'files': ['app.py', 'main.py'],
        'imports': ['fastapi', 'FastAPI'],
        'content_patterns': ['from fastapi import', 'import fastapi', 'FastAPI(', '@app.get'],
        'weight': 0.7
    },
    'tornado': {
        'imports': ['tornado'],
        'content_patterns': ['tornado.web', 'tornado.ioloop', 'RequestHandler'],
        'weight': 0.7
    },
    'aiohttp': {
        'imports': ['aiohttp'],
        'content_patterns': ['web.Application()', 'app.router.add_get', 'aiohttp.web'],
        'weight': 0.7
    },
    'bottle': {
        'imports': ['bottle'],
        'content_patterns': ['from bottle import', '@route', 'run(host='],
        'weight': 0.6
    },
    'falcon': {
        'imports': ['falcon'],
        'content_patterns': ['import falcon', 'falcon.App', 'falcon.API'],
        'weight': 0.6
    },
    'cherrypy': {
        'imports': ['cherrypy'],
        'content_patterns': ['import cherrypy', '@cherrypy.expose'],
        'weight': 0.6
    },
    'pyramid': {
        'imports': ['pyramid'],
        'content_patterns': ['from pyramid.config import', 'config.add_route'],
        'weight': 0.6
    },
    'starlette': {
        'imports': ['starlette'],
        'content_patterns': ['from starlette', 'ASGIApp'],
        'weight': 0.6
    },
    'sanic': {
        'imports': ['sanic'],
        'content_patterns': ['from sanic import', 'app = Sanic', '@app.route'],
        'weight': 0.7
    }
}

# JavaScript/Frontend Frameworks
JS_FRAMEWORKS = {
    'react': {
        'files': ['package.json', 'jsx', 'tsx', 'react-scripts', 'src/App.js', 'src/index.js'],
        'content_patterns': ['"react":', '"react-dom":', 'import React', 'from "react"', 'ReactDOM.render'],
        'imports': ['react', 'react-dom'],
        'weight': 0.9
    },
    'angular': {
        'files': ['angular.json', 'package.json', 'tsconfig.json', 'src/app/app.module.ts'],
        'content_patterns': ['"@angular/core":', 'ng new', 'ng generate', 'NgModule'],
        'weight': 0.9
    },
    'vue': {
        'files': ['vue.config.js', 'package.json'],
        'content_patterns': ['"vue":', 'new Vue(', 'createApp(', '<template>', 'export default {'],
        'imports': ['vue'],
        'weight': 0.9
    },
    'svelte': {
        'files': ['svelte.config.js', 'package.json'],
        'content_patterns': ['"svelte":', '<script>', '<style>', '$:'],
        'imports': ['svelte'],
        'weight': 0.8
    },
    'next': {
        'files': ['next.config.js', 'package.json', 'pages', 'pages/index.js'],
        'content_patterns': ['"next":', 'getStaticProps', 'getServerSideProps', 'NextPage'],
        'imports': ['next'],
        'weight': 0.8
    },
    'nuxt': {
        'files': ['nuxt.config.js', 'package.json', 'pages', 'pages/index.vue'],
        'content_patterns': ['"nuxt":', 'export default {', '<template>', 'asyncData'],
        'imports': ['nuxt'],
        'weight': 0.8
    },
    'jquery': {
        'content_patterns': ['$(', 'jQuery(', '.ready(', '.click(', '.ajax('],
        'imports': ['jquery'],
        'weight': 0.6
    },
    'backbone': {
        'content_patterns': ['Backbone.', 'Backbone.Model', 'Backbone.View'],
        'imports': ['backbone'],
        'weight': 0.6
    },
    'ember': {
        'files': ['ember-cli-build.js', 'package.json'],
        'content_patterns': ['"ember":', 'Ember.'],
        'imports': ['ember'],
        'weight': 0.7
    }
}

# Data Science Frameworks
DATA_SCIENCE_FRAMEWORKS = {
    'pytorch': {
        'imports': ['torch', 'pytorch'],
        'content_patterns': ['import torch', 'from torch import', 'torch.nn', 'torch.optim'],
        'weight': 0.8
    },
    'tensorflow': {
        'imports': ['tensorflow', 'tf'],
        'content_patterns': ['import tensorflow', 'import tf', 'tf.keras', 'tf.data'],
        'weight': 0.8
    },
    'sklearn': {
        'imports': ['sklearn', 'scikit-learn', 'scikit_learn'],
        'content_patterns': ['from sklearn import', 'sklearn.model_selection', 'train_test_split'],
        'weight': 0.7
    },
    'pandas': {
        'imports': ['pandas', 'pd'],
        'content_patterns': ['import pandas', 'pd.DataFrame', 'pd.read_csv'],
        'weight': 0.6
    },
    'numpy': {
        'imports': ['numpy', 'np'],
        'content_patterns': ['import numpy', 'np.array', 'np.zeros'],
        'weight': 0.5
    },
    'matplotlib': {
        'imports': ['matplotlib', 'plt'],
        'content_patterns': ['import matplotlib', 'plt.figure', 'plt.plot'],
        'weight': 0.5
    },
    'keras': {
        'imports': ['keras'],
        'content_patterns': ['import keras', 'keras.layers', 'Sequential'],
        'weight': 0.7
    },
    'xgboost': {
        'imports': ['xgboost'],
        'content_patterns': ['import xgboost', 'XGBClassifier', 'XGBRegressor'],
        'weight': 0.7
    },
    'lightgbm': {
        'imports': ['lightgbm'],
        'content_patterns': ['import lightgbm', 'LGBMClassifier', 'LGBMRegressor'],
        'weight': 0.7
    },
    'pyspark': {
        'imports': ['pyspark'],
        'content_patterns': ['import pyspark', 'SparkContext', 'SparkSession'],
        'weight': 0.8
    },
    'scipy': {
        'imports': ['scipy'],
        'content_patterns': ['import scipy', 'scipy.stats', 'scipy.optimize'],
        'weight': 0.5
    },
    'nltk': {
        'imports': ['nltk'],
        'content_patterns': ['import nltk', 'nltk.tokenize', 'nltk.corpus'],
        'weight': 0.7
    },
    'spacy': {
        'imports': ['spacy'],
        'content_patterns': ['import spacy', 'nlp = spacy.load'],
        'weight': 0.7
    },
    'huggingface_transformers': {
        'imports': ['transformers'],
        'content_patterns': ['from transformers import', 'AutoModel', 'AutoTokenizer'],
        'weight': 0.8
    }
}

# Testing Frameworks
TESTING_FRAMEWORKS = {
    'pytest': {
        'files': ['pytest.ini', 'conftest.py', 'test_*.py', '*_test.py'],
        'imports': ['pytest'],
        'content_patterns': ['import pytest', '@pytest.fixture', 'def test_'],
        'weight': 0.7
    },
    'unittest': {
        'imports': ['unittest'],
        'content_patterns': ['import unittest', 'unittest.TestCase', 'class Test'],
        'weight': 0.6
    },
    'nose': {
        'files': ['.noserc', 'nose.cfg'],
        'imports': ['nose'],
        'content_patterns': ['import nose', 'from nose'],
        'weight': 0.6
    },
    'jest': {
        'files': ['jest.config.js', '*.test.js', '*.spec.js'],
        'content_patterns': ['"jest":', 'describe(', 'it(', 'test(', 'expect('],
        'weight': 0.7
    },
    'mocha': {
        'files': ['mocha.opts', '.mocharc.js', '.mocharc.json'],
        'content_patterns': ['"mocha":', 'describe(', 'it(', 'before(', 'after('],
        'imports': ['mocha'],
        'weight': 0.7
    },
    'jasmine': {
        'files': ['jasmine.json', 'spec/support/jasmine.json'],
        'content_patterns': ['"jasmine":', 'describe(', 'it(', 'beforeEach('],
        'imports': ['jasmine'],
        'weight': 0.7
    },
    'cypress': {
        'files': ['cypress.json', 'cypress.config.js', 'cypress/'],
        'content_patterns': ['"cypress":', 'cy.visit', 'cy.get('],
        'imports': ['cypress'],
        'weight': 0.8
    },
    'selenium': {
        'imports': ['selenium'],
        'content_patterns': ['webdriver', 'By.', 'driver.find_element'],
        'weight': 0.7
    },
    'playwright': {
        'files': ['playwright.config.js', 'playwright.config.ts'],
        'content_patterns': ['"playwright":', 'page.goto', 'await browser.newPage'],
        'imports': ['playwright'],
        'weight': 0.8
    }
}

# Backend Frameworks and ORMs
DB_FRAMEWORKS = {
    'sqlalchemy': {
        'imports': ['sqlalchemy'],
        'content_patterns': ['from sqlalchemy import', 'Base =', 'Column(', 'relationship('],
        'weight': 0.7
    },
    'django_orm': {
        'imports': ['django.db'],
        'content_patterns': ['models.Model', 'models.CharField', 'models.ForeignKey'],
        'weight': 0.7
    },
    'peewee': {
        'imports': ['peewee'],
        'content_patterns': ['from peewee import', 'class Meta:', 'Model)'],
        'weight': 0.6
    },
    'mongoengine': {
        'imports': ['mongoengine'],
        'content_patterns': ['from mongoengine import', 'Document)', 'StringField('],
        'weight': 0.7
    },
    'prisma': {
        'files': ['schema.prisma', 'prisma/schema.prisma'],
        'content_patterns': ['generator client', 'datasource db', 'model '],
        'weight': 0.8
    },
    'sequelize': {
        'imports': ['sequelize'],
        'content_patterns': ['"sequelize":', 'const sequelize', 'define('],
        'weight': 0.7
    },
    'knex': {
        'imports': ['knex'],
        'content_patterns': ['"knex":', 'knex({', 'knex.schema'],
        'weight': 0.7
    },
    'typeorm': {
        'files': ['ormconfig.json'],
        'content_patterns': ['"typeorm":', '@Entity(', '@Column('],
        'imports': ['typeorm'],
        'weight': 0.8
    }
}

# API and GraphQL Frameworks
API_FRAMEWORKS = {
    'graphql': {
        'imports': ['graphql', 'graphene'],
        'content_patterns': ['from graphql import', 'type Query {', 'type Mutation {'],
        'weight': 0.7
    },
    'apollo': {
        'imports': ['apollo'],
        'content_patterns': ['"apollo-server":', 'ApolloServer', 'gql`'],
        'weight': 0.7
    },
    'rest_framework': {
        'imports': ['rest_framework'],
        'content_patterns': ['from rest_framework import', 'APIView', 'serializers.'],
        'weight': 0.7
    },
    'express_graphql': {
        'imports': ['express-graphql'],
        'content_patterns': ['"express-graphql":', 'graphqlHTTP'],
        'weight': 0.7
    },
    'swagger': {
        'files': ['swagger.json', 'swagger.yaml', 'openapi.yaml'],
        'content_patterns': ['swagger:', 'openapi:'],
        'weight': 0.6
    },
    'grpc': {
        'files': ['.proto'],
        'imports': ['grpc'],
        'content_patterns': ['import grpc', 'service ', 'rpc '],
        'weight': 0.8
    }
}

# DevOps and Infrastructure
DEVOPS_FRAMEWORKS = {
    'docker': {
        'files': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
        'content_patterns': ['FROM ', 'RUN ', 'COPY ', 'EXPOSE ', 'CMD ['],
        'weight': 0.8
    },
    'kubernetes': {
        'files': ['deployment.yaml', 'service.yaml', 'pod.yaml', 'k8s/'],
        'content_patterns': ['apiVersion:', 'kind: Deployment', 'kind: Service'],
        'weight': 0.8
    },
    'terraform': {
        'files': ['.tf', 'terraform.tfstate', 'terraform.tfvars'],
        'content_patterns': ['resource "', 'provider "', 'terraform {'],
        'weight': 0.8
    },
    'ansible': {
        'files': ['playbook.yml', 'ansible.cfg', 'inventory'],
        'content_patterns': ['- name:', 'hosts:', 'tasks:'],
        'weight': 0.8
    },
    'github_actions': {
        'files': ['.github/workflows/', '.github/actions/'],
        'content_patterns': ['on:', 'jobs:', 'steps:', 'uses: '],
        'weight': 0.7
    },
    'gitlab_ci': {
        'files': ['.gitlab-ci.yml'],
        'content_patterns': ['stages:', 'script:', 'image:'],
        'weight': 0.7
    },
    'jenkins': {
        'files': ['Jenkinsfile'],
        'content_patterns': ['pipeline {', 'stage(', 'agent {'],
        'weight': 0.7
    },
    'circleci': {
        'files': ['.circleci/config.yml'],
        'content_patterns': ['version: 2', 'jobs:', 'workflows:'],
        'weight': 0.7
    },
    'aws': {
        'files': ['cloudformation.yaml', 'aws-sam'],
        'content_patterns': ['AWS::', 'aws-sdk', 'boto3'],
        'imports': ['boto3', 'aws-sdk'],
        'weight': 0.6
    },
    'azure': {
        'files': ['azuredeploy.json', 'azure-pipelines.yml'],
        'content_patterns': ['Microsoft.', 'azure-', 'azure_'],
        'imports': ['azure'],
        'weight': 0.6
    },
    'gcp': {
        'files': ['app.yaml', 'Deployment.yaml'],
        'content_patterns': ['google-cloud', 'gcloud', 'GCP_'],
        'imports': ['google.cloud'],
        'weight': 0.6
    }
}

# Configuration and Build Tools
CONFIG_BUILD_TOOLS = {
    'webpack': {
        'files': ['webpack.config.js'],
        'content_patterns': ['"webpack":', 'module.exports', 'entry:', 'output:'],
        'weight': 0.7
    },
    'babel': {
        'files': ['.babelrc', 'babel.config.js'],
        'content_patterns': ['"@babel/core":', 'presets:', 'plugins:'],
        'weight': 0.7
    },
    'eslint': {
        'files': ['.eslintrc', '.eslintrc.js', '.eslintrc.json'],
        'content_patterns': ['"eslint":', 'rules:', 'extends:'],
        'weight': 0.6
    },
    'prettier': {
        'files': ['.prettierrc', '.prettierrc.js', '.prettierrc.json'],
        'content_patterns': ['"prettier":', 'tabWidth:', 'singleQuote:'],
        'weight': 0.6
    },
    'gulp': {
        'files': ['gulpfile.js'],
        'content_patterns': ['"gulp":', 'gulp.task', 'gulp.src'],
        'weight': 0.7
    },
    'grunt': {
        'files': ['Gruntfile.js'],
        'content_patterns': ['"grunt":', 'grunt.initConfig', 'grunt.registerTask'],
        'weight': 0.7
    },
    'poetry': {
        'files': ['poetry.lock', 'pyproject.toml'],
        'content_patterns': ['[tool.poetry]', 'poetry.core', 'poetry add'],
        'weight': 0.8
    },
    'setuptools': {
        'files': ['setup.py', 'setup.cfg'],
        'content_patterns': ['setuptools.setup', 'install_requires', 'packages=find_packages()'],
        'weight': 0.7
    },
    'pip': {
        'files': ['requirements.txt', 'requirements-dev.txt'],
        'content_patterns': ['pip install', 'pip freeze'],
        'weight': 0.6
    },
    'npm': {
        'files': ['package.json', 'package-lock.json'],
        'content_patterns': ['"dependencies":', '"devDependencies":', '"scripts":'],
        'weight': 0.7
    },
    'yarn': {
        'files': ['yarn.lock'],
        'content_patterns': ['"yarn":', 'yarn add', 'yarn install'],
        'weight': 0.7
    },
    'make': {
        'files': ['Makefile'],
        'content_patterns': ['.PHONY:', 'all:', 'install:', 'build:'],
        'weight': 0.6
    }
}

# Microservice indicators
MICROSERVICE_INDICATORS = {
    'docker_presence': {
        'files': ['Dockerfile', 'docker-compose.yml'],
        'weight': 1.0
    },
    'kubernetes_config': {
        'files': ['deployment.yaml', 'service.yaml', 'k8s/'],
        'weight': 1.0
    },
    'service_discovery': {
        'files': ['eureka', 'consul', 'zookeeper'],
        'content_patterns': ['discovery', 'registry', 'eureka.client'],
        'weight': 0.8
    },
    'api_gateway': {
        'files': ['gateway', 'proxy', 'ambassador'],
        'content_patterns': ['zuul', 'gateway', 'proxy_pass'],
        'weight': 0.8
    },
    'message_queue': {
        'imports': ['kafka', 'rabbitmq', 'redis', 'pubsub'],
        'content_patterns': ['queue', 'topic', 'publish', 'subscribe'],
        'weight': 0.7
    },
    'health_endpoints': {
        'content_patterns': ['/health', '/status', 'healthcheck', 'liveness'],
        'weight': 0.6
    },
    'configuration': {
        'files': ['config-server', 'consul-config'],
        'content_patterns': ['config.server', 'spring.cloud.config'],
        'weight': 0.7
    },
    'small_codebase': {
        'max_files': 50,  # Microservices tend to be smaller
        'weight': 0.5
    },
    'circuit_breaker': {
        'imports': ['hystrix', 'resilience4j', 'circuit-breaker'],
        'content_patterns': ['fallback', 'circuit', 'breaker'],
        'weight': 0.8
    }
}

# Module types based on structure
MODULE_TYPES = {
    'application': {
        'files': ['main.py', 'app.py', 'index.js', 'server.js'],
        'has_main_function': True,
        'weight': 0.8
    },
    'library': {
        'files': ['setup.py', 'package.json', 'pyproject.toml', 'requirements.txt'],
        'has_main_function': False,
        'weight': 0.7
    },
    'api': {
        'files': ['views.py', 'controllers.py', 'routes.js', 'api.py'],
        'content_patterns': ['@app.route', 'router.get', 'app.get('],
        'weight': 0.7
    },
    'data_processing': {
        'imports': ['pandas', 'numpy', 'sklearn', 'tensorflow', 'torch'],
        'content_patterns': ['DataFrame', 'np.array', 'model.fit'],
        'weight': 0.6
    },
    'cli_tool': {
        'imports': ['argparse', 'click', 'typer', 'commander'],
        'content_patterns': ['ArgumentParser', '@click.command', 'process.argv'],
        'has_main_function': True,
        'weight': 0.7
    },
    'web_frontend': {
        'files': ['index.html', 'styles.css', 'main.js', 'App.js', 'App.vue'],
        'content_patterns': ['<div', '<component', 'import React', 'createApp'],
        'weight': 0.7
    },
    'test_module': {
        'files': ['test_', '_test', 'spec.js', '.spec.ts'],
        'imports': ['pytest', 'unittest', 'jest', 'mocha'],
        'content_patterns': ['def test_', 'describe(', 'it(', 'expect('],
        'weight': 0.8
    }
}

# Key files that indicate project structure
KEY_FILES = [
    # Python
    'main.py',
    'app.py',
    'setup.py',
    'requirements.txt',
    'pyproject.toml',
    'conftest.py',
    'Pipfile',
    'pytest.ini',
    'tox.ini',
    '__init__.py',
    'models.py',
    'views.py',
    'urls.py',
    'settings.py',
    'utils.py',
    'helpers.py',
    'config.py',
    
    # JavaScript/TypeScript
    'package.json',
    'tsconfig.json',
    'index.js',
    'main.js',
    'server.js',
    'app.js',
    'webpack.config.js',
    'rollup.config.js',
    'next.config.js',
    'nuxt.config.js',
    'angular.json',
    'vue.config.js',
    
    # Configuration & Environment
    '.env',
    '.env.example',
    '.gitignore',
    '.editorconfig',
    '.prettierrc',
    '.eslintrc',
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'CONTRIBUTING.md',
    
    # CI/CD & DevOps
    'Dockerfile',
    'docker-compose.yml',
    '.gitlab-ci.yml',
    '.travis.yml',
    '.github/workflows',
    'Jenkinsfile',
    'azure-pipelines.yml',
    'cloudbuild.yaml',
    'terraform.tf',
    'serverless.yml',
    
    # Database
    'schema.sql',
    'migrations',
    'schema.prisma',
    'alembic.ini',
    'model.py',
    'entities.py',
    
    # Mobile
    'AndroidManifest.xml',
    'Info.plist',
    'build.gradle',
    'pubspec.yaml',
    'AppDelegate.swift',
    'MainActivity.java'
]

# Full Framework Dictionary
FRAMEWORK_PATTERNS = {}
FRAMEWORK_PATTERNS.update(WEB_FRAMEWORKS)
FRAMEWORK_PATTERNS.update(JS_FRAMEWORKS)
FRAMEWORK_PATTERNS.update(DATA_SCIENCE_FRAMEWORKS)
FRAMEWORK_PATTERNS.update(TESTING_FRAMEWORKS)
FRAMEWORK_PATTERNS.update(DB_FRAMEWORKS)
FRAMEWORK_PATTERNS.update(API_FRAMEWORKS)
FRAMEWORK_PATTERNS.update(DEVOPS_FRAMEWORKS)
FRAMEWORK_PATTERNS.update(CONFIG_BUILD_TOOLS)