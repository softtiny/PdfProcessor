# https://just.systems

default:
    echo 'Hello, world!'

venv:
    overlay use venv/Scripts/activate.nu

pytest:
    pytest

#Installing dependencies 

install:
    poetry install