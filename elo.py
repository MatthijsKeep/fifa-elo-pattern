def expected_outcome(rating1, rating2):
    return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

def update_elo(rating1, rating2, result1, k=32):
    expected1 = expected_outcome(rating1, rating2)
    expected2 = expected_outcome(rating2, rating1)

    new_rating1 = rating1 + k * (result1 - expected1)
    new_rating2 = rating2 + k * ((1 - result1) - expected2)

    return new_rating1, new_rating2
