#!/usr/bin/env python

import tempfile
from fpdf import FPDF
import cv2
import os
import numpy as np
import click


ARUCO_DICTIONARIES = (
    'DICT_4X4_50',
    'DICT_4X4_100',
    'DICT_4X4_250',
    'DICT_4X4_1000',

    'DICT_5X5_50',
    'DICT_5X5_100',
    'DICT_5X5_250',
    'DICT_5X5_1000',

    'DICT_6X6_50',
    'DICT_6X6_100',
    'DICT_6X6_250',
    'DICT_6X6_1000',

    'DICT_ARUCO_ORIGINAL',
)


@click.command()
@click.option('--dictionary', prompt=True, type=click.Choice(ARUCO_DICTIONARIES), help='ArUco dictionary to be used to create the board')
@click.option('--squares_x', prompt=True, type=click.INT, help='The number of squares of the board in the X direction')
@click.option('--squares_y', prompt=True, type=click.INT, help='The number of squares of the board in the Y direction')
@click.option('--square_size', prompt='Square size (mm)', type=click.FLOAT, help='The size of each square in millimeters')
@click.option('--marker_size', prompt='Marker size (mm)', type=click.FLOAT, help='The size of each marker embedded in the white squares in millimeters')
@click.option('--output_path', prompt=True, type=click.Path(writable=True), help='The path in which the PDF with the marker should be saved')
@click.option('--page_size', default='A4', show_default=True, type=click.Choice(['A4', 'Letter']), help='Page size for the PDF (A4 or Letter)')
def generate_marker(dictionary, squares_x, squares_y, square_size, marker_size, output_path, page_size):
    """Script for the generation of ChArUco marker boards"""

    square_size_m = square_size / 1000
    marker_size_m = marker_size / 1000

    complete_path = os.path.abspath(os.path.expanduser(output_path))

    INCH_TO_METER = 1 / 39.3701

    # Define page sizes in meters and pixels (height, width)
    PAGE_SIZES = {
        'A4': {
            'size_m': (0.297, 0.21),
            'resolution': (3508, 2480),
            'fpdf': 'A4',
        },
        'Letter': {
            'size_m': (11 * INCH_TO_METER, 8.5 * INCH_TO_METER),  # 11 x 8.5 inches in meters
            'resolution': (3300, 2550),  # 300 DPI: 11*300 x 8.5*300
            'fpdf': 'Letter',
        },
    }

    page_info = PAGE_SIZES[page_size]
    PAGE_SIZE_m = page_info['size_m']
    PAGE_RESOLUTION = page_info['resolution']
    PAGE_PIXELS_PER_METER = np.array(PAGE_RESOLUTION) / np.array(PAGE_SIZE_m)
    image_resolution = np.around(
        PAGE_PIXELS_PER_METER * np.array((squares_x, squares_y)) * np.array((square_size_m, square_size_m))).astype('int')

    if squares_y * square_size_m > PAGE_SIZE_m[0]:
        raise ValueError(f'given height exceeds {page_size}')
    if squares_x * square_size_m > PAGE_SIZE_m[1]:
        raise ValueError(f'given width exceeds {page_size}')
    if marker_size > square_size:
        raise ValueError('the size of the marker must be less than the size of the chessboard squares')


    aruco_dictionary_id = getattr(cv2.aruco, dictionary)
    if hasattr(cv2.aruco, 'getPredefinedDictionary'):
        aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dictionary_id)
    else:
        aruco_dict = cv2.aruco.Dictionary_get(aruco_dictionary_id)

    if hasattr(cv2.aruco, 'CharucoBoard_create'):
        board = cv2.aruco.CharucoBoard_create(squares_x, squares_y, square_size_m, marker_size_m, aruco_dict)
    else:
        board = cv2.aruco.CharucoBoard((squares_x, squares_y), square_size_m, marker_size_m, aruco_dict)

    if hasattr(board, 'draw'):
        imboard = board.draw((image_resolution[0], image_resolution[1]))
    else:
        imboard = board.generateImage((image_resolution[0], image_resolution[1]))

    f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)

    cv2.imwrite(f.name, imboard)

    board_size_x_mm = squares_x * square_size_m * 1000
    board_size_y_mm = squares_y * square_size_m * 1000

    pdf = FPDF('P', 'mm', page_info['fpdf'])
    pdf.add_page('P')

    pdf.image(
        f.name,
        x=(PAGE_SIZE_m[1] / 2 * 1000) - board_size_x_mm / 2,
        y=(PAGE_SIZE_m[0] / 2 * 1000) - board_size_y_mm / 2,
        w=board_size_x_mm,
        h=board_size_y_mm
    )

    print('Configuration:')
    print('Marker size in millimeters: ' + str(marker_size_m * 1000))
    print('Square size in millimeters: ' + str(square_size_m * 1000))
    print('Board squares: ' + str((squares_x, squares_y)))
    print('Total board size in millimeters: ' + str((board_size_x_mm, board_size_y_mm)))
    print('ArUco Dictionary name: ' + dictionary)

    print(f'Saving the marker as a {page_size} sized PDF in ' + complete_path)

    pdf.output(complete_path)

    print('REMEMBER TO TURN OFF THE AUTOMATIC RESCALING OF THE PRINTER!')


if __name__ == '__main__':
    generate_marker()
