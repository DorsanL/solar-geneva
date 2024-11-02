import pandas as pd
import pickle
import numpy as np

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy import Table, MetaData

dbname = "QBuildings-Geneva"
user = "public_user"
password = "password"
host = "128.179.39.7"
port = "4443"

engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")


def return_buildings_count():
    # Query to get the number of buildings per district
    query = """
        SELECT g.id AS district_name, COUNT(b.geometry) AS buildings_count
        FROM "Processed".geo_girec g
        LEFT JOIN "Processed".buildings b ON g.id = b.geo_girec
        GROUP BY g.id
        ORDER BY buildings_count DESC;
        """

    # Execute the query and fetch the results into a DataFrame
    df = pd.read_sql(query, engine)
    df.set_index('district_name', inplace=True)

    return df


def return_solar_potential():
    # Define the metadata and table, including the schema
    metadata = MetaData(schema="Processed")
    buildings = Table("buildings", metadata, schema="Processed", autoload_with=engine)

    # Start a session
    with Session(engine) as session:
        # Create the query
        stmt = (
            select(buildings.c.geo_girec, func.sum(buildings.c.area_roof_solar_m2).label("area_roof_solar"))
            .group_by(buildings.c.geo_girec)
        )

        # Execute the query and fetch all results
        results = session.execute(stmt).all()

    # Convert results to a DataFrame and set index to geo_girec
    df = pd.DataFrame(results, columns=["geo_girec", "area_roof_solar"]).set_index("geo_girec")
    df.index.names = ['NOM']

    # Round the values to zero decimal places
    df["pv_potential"] = df["area_roof_solar"].round(0) * 0.2

    df.to_pickle("girec_potential.pickle")

    return df
