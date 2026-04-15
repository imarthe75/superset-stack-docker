FROM prefecthq/prefect:3-latest

ARG PYPI_MIRROR=https://pypi.org/simple/
RUN pip install \
    --index-url https://pypi.org/simple/ \
    --extra-index-url $PYPI_MIRROR \
    --trusted-host $(echo $PYPI_MIRROR | awk -F[/:] '{print $4}') \
    pandas scikit-learn psycopg2-binary requests sqlalchemy \
    great-expectations dbt-expectations
