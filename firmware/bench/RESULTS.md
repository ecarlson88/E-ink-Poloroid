# Bench results

Filled in on the bench (Task 1, then Tasks 4, 6, 7 and 8). Flash `firmware/bench/bench.ino`
(board XIAO_ESP32S3, PSRAM "OPI PSRAM", Arduino-ESP32 4.0.0 or later) and use its serial menu.
The corner frame is explained in `tools/make_test_frames.py`; previews of what each frame should
look like are `corner_frame.png` and `swatch_frame.png` next to this file.

## Task 1

| Step | Question | Result |
|---|---|---|
| 1 | Does the panel's 32-pin ribbon seat in the DESPI-E01 (24-pin) through the supplied ribbon adapter? | |
| 3 | Corner frame draws (`c`) at 2 MHz, byte-at-a-time? | |
| 3 | BUSY polarity reported at start (`p`): active low or high? | |
| 4 | Which corner is red (the first byte)? Is the text mirrored? | |
| 4 | Which corner is the ribbon cable nearest? | |
| 4 | Nibble order: patch A or patch B has the even thin lines? (A = high nibble is left) | |
| 4 | So: `HIGH_NIBBLE_IS_LEFT` and `PICTURE_ROWS_FIRST` in `server/imaging.py` should be | |
| 5 | Batched writes (`m`): still draws? Transfer time at 2 / 4 / 8 / 10 MHz (`f`) | |
| 6 | Full refresh time (0x12 to BUSY release), ms | |
| 6 | Supply current during refresh / after power off (instrument: ) | |
| 6 | Panel deep-sleep current; XIAO deep sleep (`d`) with the panel asleep | |
| 7 | Wake path (`z`): second draw after panel deep sleep passes? | |

## Task 4 and later

| Measurement | Result |
|---|---|
| Awake time for one daily wake (s), supply current during it | |
| Battery reading vs multimeter at three charge levels; sag after Wi-Fi | |
| Sleep current with and without the RTC peripherals powered (edge button) | |
| Final overall case thickness | |
