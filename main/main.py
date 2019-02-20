import random
import requests

def make_pi(total):
    q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
    count = 0
    while True:
        if 4 * q + r - t < m * t:
            yield m
            count += 1
            if count > total:
                break
            q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))//t - 10*m, x
        else:
            q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)//(t*x), x+2

A_PI_ADDR = 'http://127.0.0.1:5000'
MAX_SEGMENT = 20
MIN_SEGMENT = 5

init = {'digit': '3', 'job': ''}
r = requests.post(A_PI_ADDR, data=init)
job_id = r.text

pi = make_pi(random.randint(MIN_SEGMENT, MAX_SEGMENT))
next(pi)

for digit in pi:
    payload = {'digit': str(digit), 'job': job_id}
    r = requests.post(A_PI_ADDR, data=payload)

done = {'digit': 'π', 'job': job_id}
r = requests.post(A_PI_ADDR, data=done)
