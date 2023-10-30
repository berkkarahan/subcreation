# numpy replacements
from functools import lru_cache


def average(data):
    return mean(data)


def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        return 0
    return sum(data) / float(n)


def _ss(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    ss = sum((x - c) ** 2 for x in data)
    return ss


def std(data, ddof=0):
    """Calculates the population standard deviation
    by default; specify ddof=1 to compute the sample
    standard deviation."""
    n = len(data)
    if n < 2:
        return 0
    ss = _ss(data)
    pvar = ss / (n - ddof)
    return pvar**0.5


def zeroes_float(size):
    return [0.0] * size


def zeroes_int(size):
    return [0] * size


def zeroes_float_array(size):
    output = []
    for i in range(size[0]):
        output += [[0.0] * size[1]]
    return output


def zeroes_int_array(size):
    output = []
    for i in range(size[0]):
        output += [[0] * size[1]]
    return output


def ssq(j, i, sum_x, sum_x_sq):
    if j > 0:
        muji = (sum_x[i] - sum_x[j - 1]) / (i - j + 1)
        sji = sum_x_sq[i] - sum_x_sq[j - 1] - (i - j + 1) * muji**2
    else:
        sji = sum_x_sq[i] - sum_x[i] ** 2 / (i + 1)

    return 0 if sji < 0 else sji


def fill_row_k(imin, imax, k, S, J, sum_x, sum_x_sq, N):
    if imin > imax:
        return

    i = (imin + imax) // 2
    S[k][i] = S[k - 1][i - 1]
    J[k][i] = i

    jlow = k

    if imin > k:
        jlow = int(max(jlow, J[k][imin - 1]))
    jlow = int(max(jlow, J[k - 1][i]))

    jhigh = i - 1
    if imax < N - 1:
        jhigh = int(min(jhigh, J[k][imax + 1]))

    for j in range(jhigh, jlow - 1, -1):
        sji = ssq(j, i, sum_x, sum_x_sq)

        if sji + S[k - 1][jlow - 1] >= S[k][i]:
            break

        # Examine the lower bound of the cluster border
        # compute s(jlow, i)
        sjlowi = ssq(jlow, i, sum_x, sum_x_sq)

        SSQ_jlow = sjlowi + S[k - 1][jlow - 1]

        if SSQ_jlow < S[k][i]:
            S[k][i] = SSQ_jlow
            J[k][i] = jlow

        jlow += 1

        SSQ_j = sji + S[k - 1][j - 1]
        if SSQ_j < S[k][i]:
            S[k][i] = SSQ_j
            J[k][i] = j

    fill_row_k(imin, i - 1, k, S, J, sum_x, sum_x_sq, N)
    fill_row_k(i + 1, imax, k, S, J, sum_x, sum_x_sq, N)


def fill_dp_matrix(data, S, J, K, N):
    sum_x = zeroes_float(N)
    sum_x_sq = zeroes_float(N)

    # median. used to shift the values of x to improve numerical stability
    shift = data[N // 2]

    for i in range(N):
        if i == 0:
            sum_x[0] = data[0] - shift
            sum_x_sq[0] = (data[0] - shift) ** 2
        else:
            sum_x[i] = sum_x[i - 1] + data[i] - shift
            sum_x_sq[i] = sum_x_sq[i - 1] + (data[i] - shift) ** 2

        S[0][i] = ssq(0, i, sum_x, sum_x_sq)
        J[0][i] = 0

    for k in range(1, K):
        if k < K - 1:
            imin = max(1, k)
        else:
            imin = N - 1

        fill_row_k(imin, N - 1, k, S, J, sum_x, sum_x_sq, N)


def ckmeans(data, n_clusters):
    if n_clusters <= 0:
        raise ValueError("Cannot classify into 0 or less clusters")
    if n_clusters > len(data):
        raise ValueError("Cannot generate more classes than there are data values")

    # if there's only one value, return it; there's no sensible way to split
    # it. This means that len(ckmeans([data], 2)) may not == 2. Is that OK?
    unique = len(set(data))
    if unique == 1:
        return [data]

    data.sort()
    n = len(data)

    S = zeroes_float_array((n_clusters, n))

    J = zeroes_int_array((n_clusters, n))

    fill_dp_matrix(data, S, J, n_clusters, n)

    clusters = []
    cluster_right = n - 1

    for cluster in range(n_clusters - 1, -1, -1):
        cluster_left = int(J[cluster][cluster_right])
        clusters.append(data[cluster_left : cluster_right + 1])

        if cluster > 0:
            cluster_right = cluster_left - 1

    return list(reversed(clusters))


@lru_cache
def t_interval(n):
    t_table = {}
    t_table[1] = 12.71
    t_table[2] = 4.303
    t_table[3] = 3.182
    t_table[4] = 2.776
    t_table[5] = 2.571
    t_table[6] = 2.447
    t_table[7] = 2.365
    t_table[8] = 2.306
    t_table[9] = 2.262
    t_table[10] = 2.228
    t_table[11] = 2.201
    t_table[12] = 2.179
    t_table[13] = 2.16
    t_table[14] = 2.145
    t_table[15] = 2.131
    t_table[16] = 2.12
    t_table[17] = 2.11
    t_table[18] = 2.101
    t_table[19] = 2.093
    t_table[20] = 2.086
    t_table[21] = 2.08
    t_table[22] = 2.074
    t_table[23] = 2.069
    t_table[24] = 2.064
    t_table[25] = 2.06
    t_table[26] = 2.056
    t_table[27] = 2.052
    t_table[28] = 2.048
    t_table[29] = 2.045
    t_table[30] = 2.042
    t_table[40] = 2.021
    t_table[50] = 2.009
    t_table[60] = 2
    t_table[80] = 1.99
    t_table[100] = 1.984
    t_table[120] = 1.98
    q = 1.96

    for k, v in t_table.iteritems():
        if n >= k:
            q = v

    return (-q, q)


def construct_analysis(counts, sort_by="lb_ci", limit=500):
    overall = []
    all_data = []
    for name, runs in counts.iteritems():
        for r in runs:
            all_data += [r.score]

    master_stddev = 1
    if len(all_data) >= 2:
        master_stddev = std(all_data, ddof=1)

    for name, runs in counts.iteritems():
        data = []
        max_found = 0
        max_id = ""
        max_level = 0
        all_runs = []
        for r in runs:
            data += [r.score]
            all_runs += [[r.score, r.mythic_level, r.keystone_run_id]]
            if r.score >= max_found:
                max_found = r.score
                max_id = r.keystone_run_id
                max_level = r.mythic_level
        n = len(data)
        if n == 0:
            overall += [[name, 0, 0, n, [0, 0], [0, "", 0], []]]
            continue
        mean = average(data)
        if n <= 1:
            overall += [
                [name, mean, 0, n, [0, 0], [max_found, max_id, max_level], all_runs]
            ]
            continue

        # filter to top 500
        sorted_data = sorted(data, reverse=True)
        sorted_data = sorted_data[:limit]

        stddev = std(sorted_data, ddof=1)
        sorted_mean = average(sorted_data)
        sorted_n = len(sorted_data)
        t_bounds = t_interval(n)
        ci = [
            sorted_mean + critval * master_stddev / sqrt(sorted_n)
            for critval in t_bounds
        ]

        #        stddev = std(data, ddof=1)
        #        t_bounds = t_interval(n)
        #        ci = [mean + critval * master_stddev / sqrt(n) for critval in t_bounds]
        maxi = [max_found, max_id, max_level]
        all_runs = sorted(all_runs, key=lambda x: x[0], reverse=True)
        # restrict the mean just to the runs actually used for lb_ci
        overall += [[name, sorted_mean, stddev, n, ci, maxi, all_runs]]

    overall = sorted(overall, key=lambda x: x[4][0], reverse=True)
    if sort_by == "max":
        overall = sorted(overall, key=lambda x: x[5][0], reverse=True)
    if sort_by == "n":
        overall = sorted(overall, key=lambda x: x[3], reverse=True)

    return overall
