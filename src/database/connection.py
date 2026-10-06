from sqlalchemy import create_engine


def engine_for(settings):
    return create_engine(
        settings.url,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 10},
    )
