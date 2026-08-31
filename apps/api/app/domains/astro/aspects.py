from app.domains.astro.models import Aspect, BodyPosition

ASPECTS: tuple[tuple[str, float, float], ...] = (
    ("conjunction", 0.0, 8.0),
    ("sextile", 60.0, 5.0),
    ("square", 90.0, 7.0),
    ("trine", 120.0, 7.0),
    ("opposition", 180.0, 8.0),
)


def angular_distance(first: float, second: float) -> float:
    raw = abs(first - second) % 360.0
    return min(raw, 360.0 - raw)


def calculate_aspects(bodies: tuple[BodyPosition, ...]) -> tuple[Aspect, ...]:
    aspects: list[Aspect] = []
    for index, body_a in enumerate(bodies):
        for body_b in bodies[index + 1 :]:
            separation = angular_distance(body_a.longitude, body_b.longitude)
            for kind, exact_angle, maximum_orb in ASPECTS:
                orb = abs(separation - exact_angle)
                if orb <= maximum_orb:
                    relative_speed = body_b.longitude_speed - body_a.longitude_speed
                    future_separation = angular_distance(
                        body_a.longitude + body_a.longitude_speed / 24.0,
                        body_b.longitude + body_b.longitude_speed / 24.0,
                    )
                    aspects.append(
                        Aspect(
                            body_a=body_a.body,
                            body_b=body_b.body,
                            kind=kind,
                            exact_angle=exact_angle,
                            orb=orb,
                            applying=abs(future_separation - exact_angle) < orb
                            if relative_speed != 0
                            else False,
                        )
                    )
                    break
    return tuple(aspects)
