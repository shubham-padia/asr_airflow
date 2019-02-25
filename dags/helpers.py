import sys
import os

def change_segment_id(segment_file_location, new_file_location):
    """
    In the seg file, the first field of each line is the file_id. The
    file_id should be same as the name of the segment file for the decoder
    to work.
    """

    new_file_id = os.path.splitext(os.path.basename(new_file_location))[0] 

    results = []
    with open(segment_file_location) as segment_file:
        for line in segment_file.readlines():
            result = line.split(' ')
            result[0] = new_file_id
            results.append(result)

    with open(new_file_location, 'w+') as new_file:
        for result in results:
            new_file.write(' '.join(result))
