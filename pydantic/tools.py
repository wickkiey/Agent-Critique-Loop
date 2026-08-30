"""Stub tool that gives agents a source of 'evidence' to cite during critique."""

_FACTS = {
    "sky": "Rayleigh scattering scatters shorter (blue) wavelengths of sunlight more than longer wavelengths.",
    "sunset": "At sunset, sunlight passes through more atmosphere, scattering away blue light and leaving red/orange.",
    "mars sky": "Mars' thin, dusty atmosphere scatters red light more, giving its sky a butterscotch color.",
    "rayleigh": "Rayleigh scattering intensity is proportional to 1/wavelength^4, favoring shorter wavelengths.",
}


def knowledge_lookup(query: str) -> str:
    """Return a canned fact whose key is contained in the query, or a not-found message."""
    query_lower = query.lower()
    for key, fact in _FACTS.items():
        if key in query_lower:
            return fact
    return f"No stored knowledge found for '{query}'."
