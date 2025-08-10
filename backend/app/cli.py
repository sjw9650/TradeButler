import click
from sqlalchemy import create_engine
from .models.base import Base
from .models import content as content_model
from .core.config import settings

@click.group()
def cli():
    pass

@cli.command()
def init_db():
    engine = create_engine(settings.DB_URL)
    Base.metadata.create_all(engine)
    click.echo("DB initialized.")

if __name__ == "__main__":
    cli()
