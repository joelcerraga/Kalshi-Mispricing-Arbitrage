def fit_temperature(events):
    if not events:raise ValueError('No development events')
    loss=lambda logt:np.mean([scores(calibrate(e['p'],np.exp(logt)),e['winner'])['log_loss'] for e in events])
    result=minimize_scalar(loss,bounds=(np.log(.25),np.log(4)),method='bounded',options={'xatol':1e-10})
    if not result.success:raise RuntimeError('Calibration did not converge')
    return {'temperature':float(np.exp(result.x)),'development_log_loss':float(result.fun)}
