# -*- coding: utf-8 -*-
#!/usr/bin/python
import os, re

from suffixtree import SuffixTree

class BurrowsWheeler():
    EOS = "\0"
    # EOS = "#" # a visible end marker
    
    def transform(self, s):
        """ Simplest Burrows-Wheeler transform implementation, O(n^2) respective
            to the length of the text. """
        assert self.EOS not in s, "Input string cannot contain null character (%s)" % self.EOS
        
        # add end of text marker
        s += self.EOS
        
        # table of rotated input strings
        rotations = [s[i:] + s[:i] for i in range(len(s))]
        
        # sort the table of rotations
        table = sorted(rotations)
        
        # extract the last characters of each row
        last_column = [row[-1] for row in table]
        
        # convert the characters to a string
        r = "".join(last_column)
        
        return r
    
    def inverse(self, s):
        """ Simplest Inverse Burrow-Wheeler transform implementation. """
        # make empty table for the suffix array
        table = [""] * len(s)
        
        # use lf-mapping to reverse the tranformation
        for i in range(len(s)):
            # add one letter for each partial string in the suffix array
            prepended = [s[i] + table[i] for i in range(len(s))]
            
            # convert it to sorted suffix array
            table = sorted(prepended)
            
        # Find the correct row (ending in "\0")
        for row in table:
            if row.endswith(self.EOS):
                s = row
                break
        
        # Get rid of trailing null character
        s = s.rstrip(self.EOS)
        
        return s

# ---------------------------------------------------------------------------- #
# Different Transform implementations
# ---------------------------------------------------------------------------- #

class SuffixTreeBurrowsWheeler(BurrowsWheeler):
    
    def _walk(self, node, len = 0):
        """ returns the length of suffixes ordered alphabetically """
        t = []
        for c, n in sorted(node.items()):
            if c == 0:
                t.append(len)
                continue
            k = self._walk(n, len + 1)
            t.extend(k)
        return t
        
    def transform(self, s):
        """ Burrows-Wheeler transform with SuffixTree """
        assert self.EOS not in s, "Input string cannot contain null character ('%s')" % self.EOS
        
        # add end of text marker
        s += self.EOS
        
        st = SuffixTree()
        
        # construct a suffix tree O(n * log n)
        # can also be done in O(n) time
        st.add(s)
        
        # walk inorder to find sorted suffixes
        # only get the length of each suffix
        lens = self._walk(st.root)
        
        # as the last column letter will be left of the suffix
        # this means it's len(suffix) + 1
        # from the end of the input string s
        
        r = [0]*len(lens)
        for i in xrange(len(lens)):
            l = lens[i]
            if l == len(lens):
                r[i] = self.EOS
            else:
                r[i] = s[-l-1:-l]
        return ''.join(r)

# ---------------------------------------------------------------------------- #
# Different Inverse implementations
# ---------------------------------------------------------------------------- #


def CalculateFirstOcc(s):
    """ count the letters in input string for calculating the
        first occurance of the letter in left column of the sorted
        suffix matrix """
    # s - is the bwt transformed string
    A = {} # letter count
    for i, c in enumerate(s):
        if A.get(c):
            A[c] += 1
        else:
            A[c] = 1
    
    # sort the letters
    letters = sorted(A.keys())
    
    occ = {} # first index of letter
    
    idx = 0
    for c in letters:
        occ[c] = idx
        idx += A[c]
    del idx, A
    
    return occ

class FastBurrowsWheeler(BurrowsWheeler):
    
    def inverse(self, s):
        """ Inverse Burrow-Wheeler transform based on
            "A block sorting lossless data compression algorithm"
            uses lf-mapping for rebuilding the original text.
            O(n) time, O(n*E) memory """
        
        occ = CalculateFirstOcc(s)
        
        # calculate the full lf-mapping
        # lf is mapping from input letter rank occurance to left letter
        # this shows for which idx in last column corresponds to the first idx
        lf = [0] * len(s)
        for i, c in enumerate(s):
            lf[i] = occ[c]
            occ[c] += 1
        del occ
        
        # create an empty list for storing the string
        r = ['']*(len(s)-1)
        i = 0
        
        # here we follow the lf mapping until we have the full string
        for k in xrange(len(r)-1,-1,-1):
            r[k] = s[i]
            i = lf[i]
            
        # convert it to a string
        r = ''.join(r)
        return r.rstrip(self.EOS)

def CalculateCheckpoints(s, step):
    """ count the number of letters upto some idx """
    A = {} # letter count
    C = [] # checkpoints
    for i, c in enumerate(s):
        if i % step == 0:
            C.append(A.copy())
        if A.get(c):
            A[c] += 1
        else:
            A[c] = 1
    return C

class CheckpointingBurrowsWheeler(BurrowsWheeler):
    # how often checkpoints are made
    def __init__(self, step = 20):
        self.step = max(1, step)
    
    def lf(self, s, idx, C, occ):
        # s - is the transformed text
        # idx - is the index in the tranformed string
        # C - is the checkpoint list with step 20
        # occ - is the first occurance of the letters
        
        # find the nearest checkpoint for idx
        check = (idx + (self.step / 2)) / self.step
        if check >= len(C):
            check = len(C) - 1
        pos = check * self.step
        
        letter = s[idx]
        
        # count of the letter s[idx] upto pos (not included)
        count = C[check].get(letter)
        if count == None: count = 0
        
        # range between pos and idx
        if pos < idx:
            r = xrange(pos, idx)
        else:
            r = xrange(idx, pos)
        
        # count of letters between pos, idx
        k = 0        
        for i in r:
            if letter == s[i]:
                k += 1
        
        # calculate the letter count upto idx (not included)
        if pos < idx:
            count += k
        else:
            count -= k
        
        # return the appropriate idx
        return occ[letter] + count
        
    def inverse(self, s):
        """ O(n * (step / 4) + n) time, O(n / step + step * E) memory,
            where E is the letter count """
        
        
        occ = CalculateFirstOcc(s)
        C   = CalculateCheckpoints(s, self.step)
        
        # create an empty list for storing the string
        r = [0]*(len(s)-1)
        i = 0
        
        # here we follow the lf mapping until we have the full string
        for k in xrange(len(r)-1,-1,-1):
            r[k] = s[i]
            i = self.lf(s, i, C, occ)
        
        # convert it to a string
        r = ''.join(r)
        return r.rstrip(self.EOS)
