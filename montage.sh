#!/usr/bin/env bash
montage -geometry +0+0 _output/card{000..008}.png _output/page01.png
montage -geometry +0+0 _output/card{009..017}.png _output/page02.png
montage -geometry +0+0 _output/card{018..026}.png _output/page03.png
montage -geometry +0+0 _output/card{027..035}.png _output/page04.png
montage -geometry +0+0 _output/card{036..044}.png _output/page05.png
montage -geometry +0+0 _output/card{045..053}.png _output/page06.png
montage -geometry +0+0 _output/card{054..062}.png _output/page07.png
montage -geometry +0+0 _output/card{063..071}.png _output/page08.png
montage -geometry +0+0 _output/card{072..080}.png _output/page09.png
montage -geometry +0+0 _output/card{081..089}.png _output/page10.png
montage -geometry +0+0 _output/card{090..098}.png _output/page11.png
montage -geometry +0+0 _output/card{099..107}.png _output/page12.png
convert _output/page*.png aggregated.pdf
