"""Linkvertise monetization service — wraps destination URLs for free users."""

import os
import logging
from dotenv import load_dotenv
from linkvertise import LinkvertiseClient

load_dotenv()

logger = logging.getLogger(__name__)


def create_linkvertise_url(destination_url: str) -> str:
    """
    Genera un enlace monetizado de Linkvertise a partir de una URL destino.
    Si ocurre algún error o no está configurado el ID, devuelve la URL original.
    """
    linkvertise_id_str = os.getenv("LINKVERTISE_ID")
    if not linkvertise_id_str:
        logger.warning("LINKVERTISE_ID no configurado. Se omite monetización.")
        return destination_url

    try:
        user_id = int(linkvertise_id_str)
        client = LinkvertiseClient()
        # La librería expone el método linkvertise(user_id, url)
        monetized_url = client.linkvertise(user_id, destination_url)
        logger.info(f"Linkvertise generado: {monetized_url}")
        return monetized_url
    except Exception as e:
        logger.error(f"Error al crear enlace Linkvertise: {e}")
        return destination_url
