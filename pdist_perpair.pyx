cdef inline unsigned char _mask(unsigned char c) nogil:
    if 97 <= c <= 122: # lower, upper
        c -= 32
    if   c == 65:  return 0b0001 # A
    elif c == 67:  return 0b0010  # C
    elif c == 71:  return 0b0100   # G
    elif c == 84 or c == 85: return 0b1000 # T/U
    elif c == 82:  return 0b0101 # R = A|G
    elif c == 89:  return 0b1010 # Y = C|T
    elif c == 77:  return 0b0011 # M = A|C
    elif c == 75:  return 0b1100 # K = G|T
    elif c == 83:  return 0b0110  # S = C|G
    elif c == 87:  return 0b1001  # W = A|T
    elif c == 86:  return 0b0111 # V = A|C|G
    elif c == 72:  return 0b1011  # H = A|C|T
    elif c == 68:  return 0b1101 # D = A|G|T
    elif c == 66:  return 0b1110   # B = C|G|T
    elif c == 78:  return 0b1111   # N = A|C|G|T
    return 0 

cpdef double measurepair_distancem(bytes seq1, bytes seq2, int minoverlap):
    cdef Py_ssize_t n = len(seq1)
    if n != len(seq2):
        return -1.0

    cdef Py_ssize_t i
    cdef unsigned char a, b, ma, mb
    cdef Py_ssize_t num_d = 0
    cdef Py_ssize_t num_s = 0
    cdef Py_ssize_t compared

    for i in range(n):
        a = seq1[i]; b = seq2[i]
        if a == 45 or b == 45 or a == 63 or b == 63:  # '-' or '?'
            continue
        ma = _mask(a)
        if ma == 0:
            continue

        mb = _mask(b)
        if mb == 0:
            num_d += 1
            continue

        if (ma & mb) != 0:
            num_s += 1
        else:
            num_d += 1

    compared = num_d + num_s
    if compared <= minoverlap:
        return -1.0
    return num_d / (<double>compared)
