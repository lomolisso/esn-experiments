def default_mean(data):
    return data.mean()

def pondered_mean(data):
    return (data * data.index).sum() / data.sum()

