class MetricsEntity:
    """
    Entity class that represents an analysis' metrics
    """

    area_left_lung: float
    area_right_lung: float
    asymmetry_score: float
    is_asymmetry_critical: bool

    def __init__(self, area_left_lung: float, area_right_lung: float, asymmetry_score: float, is_asymmetry_critical: bool | None = None):
        self.area_left_lung = area_left_lung
        self.area_right_lung = area_right_lung
        self.asymmetry_score = asymmetry_score
        if is_asymmetry_critical is None:
            self.is_asymmetry_critical = asymmetry_score > 0.25 or asymmetry_score < 0.0
        else:
            self.is_asymmetry_critical = is_asymmetry_critical