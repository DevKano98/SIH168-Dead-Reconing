# IO-VNBD dataset catalog

## Scope and method

This catalog describes the **extracted files currently in this workspace**. All 564 CSVs were read to the end with a CSV parser. For each file, the scan recorded exact header order, data-row count, field-count errors, blank/`NaN`/`null`/`none` cells, numeric versus text values, numeric minima and maxima, and text examples. The 161 JPGs were opened to read their dimensions; both ZIP directories were inspected. Paths below reflect the extraction's repeated top-level folder name (for example, `Synchronised V abd S datasets/Synchronised V abd S datasets/...`). Header spelling, spacing, and case are preserved from the CSVs; some headers mix UTF-8 and single-byte characters, which were decoded for display.

| Item | Files | Detail |
| --- | ---: | --- |
| Vehicle CSVs | 323 | One 29-column schema |
| Smartphone CSVs | 241 | Five schema variants |
| JPG route images | 161 | All opened as JPEG |
| ZIP archives | 2 | Both readable |
| CSV rows across all copies | 9,189,756 | Includes categorized/uncategorized and synchronized/unsynchronized copies |
| CSV rows after exact-file deduplication | 5,555,423 | 329 distinct CSV byte streams |

SHA-256 comparison found 418 distinct CSV/JPG byte streams among 725 extracted CSV/JPG files (307 repeated copies). File rows are listed individually below because their location in the dataset structure still matters. Row totals across copies should not be interpreted as independent driving observations.

## Dataset context

The accompanying [README_1.pdf](README_1.pdf) describes IO-VNBD as vehicle CAN bus/GPS (`V-`) and smartphone inertial/GPS (`S-`) recordings. It reports about 40 hours/1,300 km of vehicle driving and 58 hours/4,400 km of smartphone driving. The vehicle logger and phone inertial sensors are described as approximately 10 Hz, with phone GPS updating at about 1 Hz. The synchronized branch contains manually aligned simultaneous V/S runs where available. The categorized folders organize runs by driver and often pair the CSVs with a route JPG. The flat uncategorized folders repeat many of those runs. Vehicle runs were collected in England; phone-only runs also include France and Nigeria. These descriptions come from the paper; the counts and schemas in this catalog come from the actual extracted files.

Drivers A, B, C, D, F, G, and H are described as defensive and E as aggressive. The publication's Tables A1-1–A7 give run-level dates, conditions, routes, durations, distances, and point counts; those figures are source claims and may differ from the parsed CSV row counts below.

## Exact CSV schemas and column profiles

Schema IDs in the inventory refer to the following **exact header sequences**. Numeric ranges and blank counts combine all files with that schema, including duplicate copies. `Numeric` means every populated value parsed as a number; `Text` means no populated value parsed as a number; `Mixed` means both appeared. The parser treats empty strings and case-insensitive `NaN`, `null`, and `none` as missing. It does not validate physical plausibility or repair values. Text examples are representative, not exhaustive.

| Schema | Description | Files | Rows across copies | Blank cells |
| --- | --- | ---: | ---: | ---: |
| S1 | Vehicle, 29 fields | 323 | 4,972,950 | 0 |
| S2 | Phone, Yaw/Pitch/Roll labels, 24 fields | 158 | 2,502,994 | 2,716 |
| S3 | Phone, X/Y/Z labels, 24 fields | 71 | 998,549 | 98 |
| S4 | Phone, 18 fields (no magnetic/orientation fields) | 9 | 603,425 | 0 |
| S5 | Phone, X/Y/Z labels and shortened Date header, 24 fields | 2 | 79,009 | 0 |
| S6 | Phone, 24 named fields plus unnamed numeric field | 1 | 32,829 | 32,829 |

### S1: Vehicle, 29 fields

Found in 323 file(s). Example: `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/M (Driver B)/V-M.csv`.

| # | Exact column header | Observed type | Missing cells | Observed numeric range / text example |
| ---: | --- | --- | ---: | --- |
| 1 | `No of GPS Satellites Available` | Numeric | 0 | 0 to 140 |
| 2 | ` Time Since Start of Day (seconds)` | Numeric | 0 | 29,606.4 to 72,986.1 |
| 3 | ` Latitude (degrees)` | Numeric | 0 | 51.6603 to 53.7951 |
| 4 | ` Longitude (degrees)` | Numeric | 0 | -2.25355 to -0.602613 |
| 5 | ` Velocity (km/hr)` | Numeric | 0 | 0 to 131.879 |
| 6 | ` Heading (degrees)` | Numeric | 0 | 0 to 360 |
| 7 | ` Height (km)` | Numeric | 0 | 20.19 to 534.26 |
| 8 | ` Vertical velocity (km/hr)` | Numeric | 0 | -15.95 to 13.53 |
| 9 | ` Sample period (seconds)` | Numeric | 0 | 0.099 to 0.2 |
| 10 | ` Steering Angle (degrees)` | Numeric | 0 | 0 to 800.8 |
| 11 | ` Wheel Speed Front Left (rad/sec)` | Numeric | 0 | 0 to 131.33 |
| 12 | ` Wheel Speed Front Right (rad/sec)` | Numeric | 0 | 0 to 131.47 |
| 13 | ` Wheel Speed Rear Left (rad/sec)` | Numeric | 0 | 0 to 131.66 |
| 14 | ` Wheel Speed Rear Right (rad/sec)` | Numeric | 0 | 0 to 130.81 |
| 15 | ` Yaw Rate (deg/sec)` | Numeric | 0 | -66 to 66.6 |
| 16 | ` Indicated Vehicle Speed (km/hr)` | Numeric | 0 | 0 to 131.36 |
| 17 | ` Indicated Longitudinal Acceleration (g)` | Numeric | 0 | -1.01082 to 0.48042 |
| 18 | ` Indicated Lateral Acceleration (g)` | Numeric | 0 | -0.90066 to 0.87006 |
| 19 | ` Handbrake (0 or 1)` | Numeric | 0 | 0 to 1 |
| 20 | ` Gear Requested (Number fof gear employed 1-5)` | Numeric | 0 | 0 to 14 |
| 21 | ` Gear (Number fof gear employed 1-5)` | Numeric | 0 | 0 to 5 |
| 22 | ` Engine Speed (rev/min)` | Numeric | 0 | 0 to 6,332 |
| 23 | ` Coolant Temperature (degrees)` | Numeric | 0 | 0 to 105 |
| 24 | ` Clutch Position (0 or 1)` | Numeric | 0 | 0 to 0 |
| 25 | ` Brake Pressure (psi)` | Numeric | 0 | -1.91 to 192.85 |
| 26 | ` Brake Position (0 or 1)` | Numeric | 0 | 0 to 1 |
| 27 | ` Battery Voltage (volts)` | Numeric | 0 | 0 to 14.6 |
| 28 | ` Air Temperature (degrees)` | Numeric | 0 | 0 to 30.75 |
| 29 | ` Accelerator Pedal Position (0 or 1)` | Numeric | 0 | 0 to 99 |

### S2: Phone, Yaw/Pitch/Roll labels, 24 fields

Found in 158 file(s). Example: `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/M (Driver B)/S-M.csv`.

| # | Exact column header | Observed type | Missing cells | Observed numeric range / text example |
| ---: | --- | --- | ---: | --- |
| 1 | `GPS LATITUDE (degrees)` | Numeric | 0 | 6.44291 to 53.7928 |
| 2 | ` GPS LONGITUDE (degrees)` | Numeric | 0 | -5.03313 to 3.41029 |
| 3 | ` GPS ALTITUDE (m)` | Numeric | 0 | 0 to 864.52 |
| 4 | ` GPS SPEED (Kmh)` | Numeric | 8 | -0.18 to 125.78 |
| 5 | ` GPS ACCURACY (m)` | Numeric | 0 | 1 to 3,911 |
| 6 | ` GPS ORIENTATION (°)` | Numeric | 2,708 | 0 to 360 |
| 7 | `GPS SATELLITES IN RANGE` | Text | 0 | e.g. `18 / 19` |
| 8 | ` TIME SINCE START (ms)` | Numeric | 0 | 5 to 1.45027e+07 |
| 9 | ` DATE (YYYY-MO-DD HH-MI-SS_SSS)` | Text | 0 | e.g. `2019-09-07 09:13:29:506` |
| 10 | ` ACCELEROMETER X (m/s²) ` | Numeric | 0 | -49.1996 to 26.1168 |
| 11 | ` ACCELEROMETER Y (m/s²)` | Numeric | 0 | -39.3612 to 52.3986 |
| 12 | ` ACCELEROMETER Z (m/s²)` | Numeric | 0 | -28.0714 to 59.4461 |
| 13 | ` GRAVITY X (m/s²)` | Numeric | 0 | -4.6387 to 3.2348 |
| 14 | ` GRAVITY Y (m/s²)` | Numeric | 0 | -6.3672 to 4.8688 |
| 15 | ` GRAVITY Z (m/s²)` | Numeric | 0 | 7.0634 to 9.8067 |
| 16 | ` GYROSCOPE Yaw (rad/s)` | Numeric | 0 | -13.5066 to 13.692 |
| 17 | ` GYROSCOPE Pitch (rad/s)` | Numeric | 0 | -10.8728 to 20.0112 |
| 18 | ` GYROSCOPE Roll (rad/s)` | Numeric | 0 | -7.1924 to 12.8719 |
| 19 | ` MAGNETIC FIELD X (μT)` | Numeric | 0 | -107.5 to 58 |
| 20 | ` MAGNETIC FIELD Y (μT)` | Numeric | 0 | -170.75 to 53.46 |
| 21 | ` MAGNETIC FIELD Z (μT)` | Numeric | 0 | -64.62 to 159.44 |
| 22 | ` ORIENTATION (Yaw) (°)` | Numeric | 0 | -0.14 to 360 |
| 23 | ` ORIENTATION (Pitch) (°)` | Numeric | 0 | -90 to 109.56 |
| 24 | ` ORIENTATION (Roll ) (°)` | Numeric | 0 | -180 to 180 |

### S3: Phone, X/Y/Z labels, 24 fields

Found in 71 file(s). Example: `Synchronised V abd S datasets/Synchronised V abd S datasets/Uncategorised IOVNB Dataset/S-Dataset/S-M.csv`.

| # | Exact column header | Observed type | Missing cells | Observed numeric range / text example |
| ---: | --- | --- | ---: | --- |
| 1 | `GPS LATITUDE (degrees)` | Numeric | 0 | 51.9464 to 53.281 |
| 2 | ` GPS LONGITUDE (degrees)` | Numeric | 0 | -2.25346 to -0.602715 |
| 3 | ` GPS ALTITUDE (m)` | Numeric | 0 | 0 to 441.65 |
| 4 | ` GPS SPEED (Kmh)` | Numeric | 4 | -0.18 to 35.81 |
| 5 | ` GPS ACCURACY (m)` | Numeric | 0 | 1 to 2,400 |
| 6 | ` GPS ORIENTATION (°)` | Numeric | 94 | 0 to 360 |
| 7 | `GPS SATELLITES IN RANGE` | Text | 0 | e.g. `18 / 19` |
| 8 | ` TIME SINCE START (ms)` | Numeric | 0 | 5 to 1.45027e+07 |
| 9 | ` DATE (YYYY-MO-DD HH-MI-SS_SSS)` | Text | 0 | e.g. `2019-09-07 09:13:29:506` |
| 10 | ` ACCELEROMETER X (m/s²) ` | Numeric | 0 | -49.1996 to 26.1168 |
| 11 | ` ACCELEROMETER Y (m/s²)` | Numeric | 0 | -39.3612 to 52.3986 |
| 12 | ` ACCELEROMETER Z (m/s²)` | Numeric | 0 | -28.0714 to 59.4461 |
| 13 | ` GRAVITY X (m/s²)` | Numeric | 0 | -4.6387 to 2.3908 |
| 14 | ` GRAVITY Y (m/s²)` | Numeric | 0 | -6.3672 to 4.8688 |
| 15 | ` GRAVITY Z (m/s²)` | Numeric | 0 | 7.0634 to 9.8067 |
| 16 | ` GYROSCOPE X (rad/s)` | Numeric | 0 | -13.5066 to 13.692 |
| 17 | ` GYROSCOPE Y (rad/s)` | Numeric | 0 | -10.8728 to 20.0112 |
| 18 | ` GYROSCOPE Z (rad/s)` | Numeric | 0 | -7.1924 to 12.8719 |
| 19 | ` MAGNETIC FIELD X (μT)` | Numeric | 0 | -107.5 to 58 |
| 20 | ` MAGNETIC FIELD Y (μT)` | Numeric | 0 | -170.75 to 53.46 |
| 21 | ` MAGNETIC FIELD Z (μT)` | Numeric | 0 | -64.62 to 159.44 |
| 22 | ` ORIENTATION (Azimuth) (°)` | Numeric | 0 | 0 to 360 |
| 23 | ` ORIENTATION (Pitch) (°)` | Numeric | 0 | -90 to 84.27 |
| 24 | ` ORIENTATION (Roll ) (°)` | Numeric | 0 | -180 to 180 |

### S4: Phone, 18 fields (no magnetic/orientation fields)

Found in 9 file(s). Example: `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Uncategorised IOVNB (V and S) Dataset/S-Dataset/S-T1.csv`.

| # | Exact column header | Observed type | Missing cells | Observed numeric range / text example |
| ---: | --- | --- | ---: | --- |
| 1 | `GPS LATITUDE (degrees)` | Numeric | 0 | 45.6237 to 48.5068 |
| 2 | `GPS LONGITUDE (degrees)` | Numeric | 0 | -2.72495 to 0.227605 |
| 3 | ` GPS ALTITUDE (m)` | Numeric | 0 | 21.41 to 226.32 |
| 4 | `GPS SPEED (Kmh)` | Numeric | 0 | 0 to 39.32 |
| 5 | `GPS ACCURACY (m)` | Numeric | 0 | 3.216 to 56.1 |
| 6 | `GPS ORIENTATION (°)` | Numeric | 0 | 0 to 359.8 |
| 7 | ` SATELLITES IN RANGE` | Text | 0 | e.g. `17 / 23` |
| 8 | ` TIME SINCE START (ms)` | Numeric | 0 | 9 to 1.01701e+07 |
| 9 | ` DATE (YYYY-MO-DD HH-MI-SS_SSS)` | Text | 0 | e.g. `2019-08-08 09:14:27:556` |
| 10 | `ACCELEROMETER X (m/s²) ` | Numeric | 0 | -10.1896 to 17.4823 |
| 11 | ` ACCELEROMETER Y (m/s²)` | Numeric | 0 | -12.4801 to 25.6062 |
| 12 | ` ACCELEROMETER Z (m/s²)` | Numeric | 0 | -6.6755 to 31.8397 |
| 13 | ` GRAVITY X (m/s²)` | Numeric | 0 | -5.0986 to 9.7712 |
| 14 | ` GRAVITY Y (m/s²)` | Numeric | 0 | -5.4943 to 8.8471 |
| 15 | ` GRAVITY Z (m/s²)` | Numeric | 0 | -6.0228 to 9.8067 |
| 16 | ` GYROSCOPE Yaw (rad/s)` | Numeric | 0 | -5.0742 to 5.2024 |
| 17 | ` GYROSCOPE Pitch (rad/s)` | Numeric | 0 | -6.369 to 6.4951 |
| 18 | ` GYROSCOPE Roll (rad/s)` | Numeric | 0 | -6.3607 to 4.0565 |

### S5: Phone, X/Y/Z labels and shortened Date header, 24 fields

Found in 2 file(s). Example: `Synchronised V abd S datasets/Synchronised V abd S datasets/Uncategorised IOVNB Dataset/S-Dataset/S-Vfa01.csv`.

| # | Exact column header | Observed type | Missing cells | Observed numeric range / text example |
| ---: | --- | --- | ---: | --- |
| 1 | `GPS LATITUDE (degrees)` | Numeric | 0 | 52.5595 to 53.7928 |
| 2 | ` GPS LONGITUDE (degrees)` | Numeric | 0 | -1.77041 to -1.23112 |
| 3 | ` GPS ALTITUDE (m)` | Numeric | 0 | 92.94 to 253.65 |
| 4 | ` GPS SPEED (Kmh)` | Numeric | 0 | 0 to 31.82 |
| 5 | ` GPS ACCURACY (m)` | Numeric | 0 | 2 to 8 |
| 6 | ` GPS ORIENTATION (°)` | Numeric | 0 | 0.29 to 359.82 |
| 7 | `GPS SATELLITES IN RANGE` | Text | 0 | e.g. `25 / 25` |
| 8 | ` TIME SINCE START (ms)` | Numeric | 0 | 38 to 6.75224e+06 |
| 9 | ` DATE (YYYY-MO-DD HH-MI-SS_SSS` | Text | 0 | e.g. `2019-11-08 09:20:26:236` |
| 10 | ` ACCELEROMETER X (m/s²) ` | Numeric | 0 | -15.1118 to 16.5209 |
| 11 | ` ACCELEROMETER Y (m/s²)` | Numeric | 0 | -10.8842 to 11.065 |
| 12 | ` ACCELEROMETER Z (m/s²)` | Numeric | 0 | 1.122 to 16.767 |
| 13 | ` GRAVITY X (m/s²)` | Numeric | 0 | -0.2087 to 0.2104 |
| 14 | ` GRAVITY Y (m/s²)` | Numeric | 0 | -0.2095 to 0.2415 |
| 15 | ` GRAVITY Z (m/s²)` | Numeric | 0 | 9.8024 to 9.8066 |
| 16 | ` GYROSCOPE X (rad/s)` | Numeric | 0 | -0.6392 to 0.7377 |
| 17 | ` GYROSCOPE Y (rad/s)` | Numeric | 0 | -1.9187 to 1.5591 |
| 18 | ` GYROSCOPE Z (rad/s)` | Numeric | 0 | -1.0892 to 1.6351 |
| 19 | ` MAGNETIC FIELD X (μT)` | Numeric | 0 | -42.94 to 27.31 |
| 20 | ` MAGNETIC FIELD Y (μT)` | Numeric | 0 | -97.37 to 5.88 |
| 21 | ` MAGNETIC FIELD Z (μT)` | Numeric | 0 | -5.62 to 91.31 |
| 22 | ` ORIENTATION (Azimuth) (°)` | Numeric | 0 | 0 to 360 |
| 23 | ` ORIENTATION (Pitch) (°)` | Numeric | 0 | -89.94 to -72.67 |
| 24 | ` ORIENTATION (Roll ) (°)` | Numeric | 0 | -180 to 180 |

### S6: Phone, 24 named fields plus unnamed numeric field

Found in 1 file(s). Example: `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Uncategorised IOVNB (V and S) Dataset/S-Dataset/S-A4.csv`.

| # | Exact column header | Observed type | Missing cells | Observed numeric range / text example |
| ---: | --- | --- | ---: | --- |
| 1 | `GPS LATITUDE (degrees)` | Numeric | 0 | 51.8193 to 52.1857 |
| 2 | ` GPS LONGITUDE (degrees)` | Numeric | 0 | -2.22364 to -1.87714 |
| 3 | ` GPS ALTITUDE (m)` | Numeric | 0 | 0 to 95 |
| 4 | ` GPS SPEED (Kmh)` | Numeric | 0 | 0 to 29.13 |
| 5 | ` GPS ACCURACY (m)` | Numeric | 0 | 3 to 1,400 |
| 6 | ` GPS ORIENTATION (°)` | Numeric | 0 | 0 to 353.9 |
| 7 | `GPS SATELLITES IN RANGE` | Empty | 32,829 | — |
| 8 | ` TIME SINCE START (ms)` | Text | 0 | e.g. `13 / 24` |
| 9 | ` DATE (YYYY-MO-DD HH-MI-SS_SSS)` | Numeric | 0 | 45 to 3.28284e+06 |
| 10 | ` ACCELEROMETER X (m/s²) ` | Text | 0 | e.g. `2019-08-16 11:29:24:414` |
| 11 | ` ACCELEROMETER Y (m/s²)` | Numeric | 0 | -2.648 to 3.5993 |
| 12 | ` ACCELEROMETER Z (m/s²)` | Numeric | 0 | -2.5708 to 2.3883 |
| 13 | ` GRAVITY X (m/s²)` | Numeric | 0 | 5.4996 to 14.7455 |
| 14 | ` GRAVITY Y (m/s²)` | Numeric | 0 | -0.5262 to 0.4677 |
| 15 | ` GRAVITY Z (m/s²)` | Numeric | 0 | -0.3974 to 0.4094 |
| 16 | ` GYROSCOPE Yaw (rad/s)` | Numeric | 0 | 9.784 to 9.8067 |
| 17 | ` GYROSCOPE Pitch (rad/s)` | Numeric | 0 | -0.229 to 0.2216 |
| 18 | ` GYROSCOPE Roll (rad/s)` | Numeric | 0 | -0.2277 to 0.3207 |
| 19 | ` MAGNETIC FIELD X (μT)` | Numeric | 0 | -0.3579 to 0.3643 |
| 20 | ` MAGNETIC FIELD Y (μT)` | Numeric | 0 | -38.97 to 26.84 |
| 21 | ` MAGNETIC FIELD Z (μT)` | Numeric | 0 | -29.55 to 34.78 |
| 22 | ` ORIENTATION (Yaw) (°)` | Numeric | 0 | -59.74 to 29.21 |
| 23 | ` ORIENTATION (Pitch) (°)` | Numeric | 0 | 34.29 to 356.36 |
| 24 | ` ORIENTATION (Roll ) (°)` | Numeric | 0 | -10.82 to 20.47 |
| 25 | `` | Numeric | 0 | -19.34 to 20.05 |

## Findings that affect analysis

- **Semantic alignment warning for `S-A4.csv`:** a targeted inspection shows a blank field at position 7, a satellite string at position 8, elapsed milliseconds at position 9, and a date string at position 10. This is consistent with an inserted empty data field shifting subsequent values one column to the right; the unnamed final value may be the displaced Roll value. The raw S6 profile above is descriptive, not a usable semantic mapping. Quarantine this file until a full-file, logged repair verifies the shifted mapping. Equal row widths did not detect this problem.
- **Six exact header layouts:** the 29-column vehicle schema is consistent across all 323 vehicle CSVs. Phone files use 24-column Yaw/Pitch/Roll, 24-column X/Y/Z, 18-column, shortened-Date-header, and 25-column variants. The 25-column file has an apparent value/header shift described above. Compare and semantically validate headers before concatenating files.
- **Gyroscope labels:** the PDF repeats `Gyroscope (Pitch)` for its third gyroscope axis. The actual common phone CSVs label the third axis `GYROSCOPE Roll (rad/s)`; another variant uses X/Y/Z. The orientation field order is Yaw, Pitch, Roll in the files, while the PDF table orders Roll before Pitch.
- **Incomplete phone columns:** the nine 18-column `S-T*.csv` files omit magnetic field and orientation columns. `S-A4.csv` has an extra unnamed 25th column populated with numeric values in all 32,829 rows (observed range −19.34 to 20.05); its `GPS SATELLITES IN RANGE` field is empty throughout. The meaning of the extra column is unknown.
- **Blank values:** only six CSV files contain any blank cells by this scan. Outside `S-A4.csv`, blanks occur in `GPS ORIENTATION` for `S-A5.csv` (700), `S-A6.csv` (1,820), and three copies of `S-Y1.csv` (94 each); the three `S-Y1.csv` copies also have four blank `GPS SPEED` cells each. These counts include duplicate copies.
- **All rows have the expected field count:** the scan found zero rows with more or fewer fields than their file's header. This does not guarantee valid sensor values or timestamps.
- **Questionable printed units/ranges:** the vehicle header says `Height (km)` while observed values span 20.19–534.26; `Gear Requested` says 1–5 but values span 0–14; `Accelerator Pedal Position` says `(0 or 1)` but values span 0–99. Retain the raw values and verify semantics before conversion or modeling.
- **Satellite field format:** many phone `SATELLITES IN RANGE` values are text such as `18 / 19`, rather than a single numeric count. Parse only after defining what each side represents. `S-T7.csv` exists in the extracted data, although Table A7's short list of French runs omits T7.

## Complete extracted file inventory

Each CSV row below gives the parsed data-row count, exact schema ID, count of missing cells across its columns, and file size. Each JPG row gives pixel dimensions. ZIP rows give the number of archived files. Every listed file was present and readable during this scan. The nested folder names are literal current paths.

### `.`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `Synchronised V abd S datasets.zip` | ZIP archive | 360 files | — | — | 203,606,286 |
| `Unsynchronised V and S Dataset.zip` | ZIP archive | 366 files | — | — | 214,330,231 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/M (Driver B)`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-M.csv` | Phone CSV | 105,974 | S2 | 0 | 19,798,721 |
| `V-M.csv` | Vehicle CSV | 105,974 | S1 | 0 | 22,507,823 |
| `V-M.JPG` | Route JPG | 741 × 611 | — | — | 132,217 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-S1.csv` | Phone CSV | 51,746 | S2 | 0 | 9,631,499 |
| `V-S1.csv` | Vehicle CSV | 51,746 | S1 | 0 | 10,967,129 |
| `V-S1.JPG` | Route JPG | 1088 × 580 | — | — | 207,995 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S2`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-S2.csv` | Phone CSV | 93,876 | S2 | 0 | 17,469,302 |
| `V-S2.csv` | Vehicle CSV | 93,876 | S1 | 0 | 20,091,681 |
| `V-S2.JPG` | Route JPG | 847 × 634 | — | — | 133,093 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S3a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-S3a.csv` | Phone CSV | 24,621 | S2 | 0 | 4,580,130 |
| `V-S3a.csv` | Vehicle CSV | 24,621 | S1 | 0 | 5,286,764 |
| `V-S3a.JPG` | Route JPG | 1087 × 621 | — | — | 169,114 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S3b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-S3b.csv` | Phone CSV | 6,813 | S2 | 0 | 1,253,565 |
| `V-S3b.csv` | Vehicle CSV | 6,813 | S1 | 0 | 1,464,196 |
| `V-S3b.JPG` | Route JPG | 555 × 610 | — | — | 132,557 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S3c`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-S3c.csv` | Phone CSV | 37,183 | S2 | 0 | 6,881,631 |
| `V-S3c.csv` | Vehicle CSV | 37,183 | S1 | 0 | 7,976,092 |
| `V-S3c.JPG` | Route JPG | 856 × 649 | — | — | 141,869 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S4`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-S4.csv` | Phone CSV | 94,600 | S2 | 0 | 17,574,514 |
| `V-S4.csv` | Vehicle CSV | 94,600 | S1 | 0 | 20,164,189 |
| `V-S4.JPG` | Route JPG | 602 × 632 | — | — | 123,854 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vf (Driver E)/V-Vfa01`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vfa01.csv` | Phone CSV | 11,486 | S2 | 0 | 2,134,667 |
| `V-Vfa01.csv` | Vehicle CSV | 11,535 | S1 | 0 | 2,398,099 |
| `V-Vfa01.JPG` | Route JPG | 837 × 637 | — | — | 103,673 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vf (Driver E)/V-Vfa02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vfa02.csv` | Phone CSV | 67,523 | S2 | 0 | 12,603,657 |
| `V-Vfa02.csv` | Vehicle CSV | 67,755 | S1 | 0 | 13,955,001 |
| `V-Vfa02.JPG` | Route JPG | 603 × 653 | — | — | 103,932 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta01a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta1a.csv` | Phone CSV | 25,676 | S2 | 0 | 4,766,740 |
| `V-Vta1a.csv` | Vehicle CSV | 25,676 | S1 | 0 | 5,444,513 |
| `V-Vta1a.JPG` | Route JPG | 721 × 648 | — | — | 125,542 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta01b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta1b.csv` | Phone CSV | 954 | S2 | 0 | 178,260 |
| `V-Vta1b.csv` | Vehicle CSV | 953 | S1 | 0 | 205,277 |
| `V-Vta1b.JPG` | Route JPG | 469 × 614 | — | — | 53,683 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta2.csv` | Phone CSV | 10,991 | S2 | 0 | 2,038,713 |
| `V-vta2.csv` | Vehicle CSV | 10,991 | S1 | 0 | 2,307,461 |
| `V-Vta2.JPG` | Route JPG | 715 × 667 | — | — | 137,726 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta03`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta3.csv` | Phone CSV | 645 | S2 | 0 | 116,809 |
| `V-vta3.csv` | Vehicle CSV | 645 | S1 | 0 | 137,891 |
| `V-Vta3.JPG` | Route JPG | 1083 × 457 | — | — | 138,187 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta04`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta4.csv` | Phone CSV | 1,789 | S2 | 0 | 331,302 |
| `V-vta4.csv` | Vehicle CSV | 1,789 | S1 | 0 | 380,874 |
| `V-Vta4.JPG` | Route JPG | 575 × 603 | — | — | 124,092 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta05`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta5.csv` | Phone CSV | 307 | S2 | 0 | 57,485 |
| `V-vta5.csv` | Vehicle CSV | 307 | S1 | 0 | 66,401 |
| `V-Vta5.JPG` | Route JPG | 703 × 627 | — | — | 115,310 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta06`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta6.csv` | Phone CSV | 1,376 | S2 | 0 | 254,665 |
| `V-Vta4.JPG` | Route JPG | 575 × 603 | — | — | 124,092 |
| `V-vta6.csv` | Vehicle CSV | 1,376 | S1 | 0 | 289,249 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta07`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta7.csv` | Phone CSV | 840 | S2 | 0 | 155,360 |
| `V-vta7.csv` | Vehicle CSV | 840 | S1 | 0 | 179,784 |
| `V-Vta7.JPG` | Route JPG | 602 × 607 | — | — | 90,532 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta08`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta8.csv` | Phone CSV | 3,676 | S2 | 0 | 678,900 |
| `V-vta8.csv` | Vehicle CSV | 3,676 | S1 | 0 | 753,939 |
| `V-Vta8.JPG` | Route JPG | 612 × 668 | — | — | 93,238 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta09`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta9.csv` | Phone CSV | 156 | S2 | 0 | 29,554 |
| `V-vta9.csv` | Vehicle CSV | 156 | S1 | 0 | 33,110 |
| `V-Vta9.JPG` | Route JPG | 1087 × 552 | — | — | 128,689 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta10`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta10.csv` | Phone CSV | 1,502 | S2 | 0 | 279,232 |
| `V-vta10.csv` | Vehicle CSV | 1,502 | S1 | 0 | 317,921 |
| `V-Vta10.JPG` | Route JPG | 862 × 642 | — | — | 103,718 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta11`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta11.csv` | Phone CSV | 510 | S2 | 0 | 95,272 |
| `V-vta11.csv` | Vehicle CSV | 510 | S1 | 0 | 111,690 |
| `V-Vta11.JPG` | Route JPG | 700 × 601 | — | — | 50,368 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta12`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta12.csv` | Phone CSV | 610 | S2 | 0 | 114,418 |
| `V-vta12.csv` | Vehicle CSV | 610 | S1 | 0 | 128,904 |
| `V-Vta12.JPG` | Route JPG | 640 × 626 | — | — | 54,434 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta13`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta13.csv` | Phone CSV | 404 | S2 | 0 | 76,217 |
| `V-vta13.csv` | Vehicle CSV | 404 | S1 | 0 | 86,963 |
| `V-Vta13.JPG` | Route JPG | 669 × 590 | — | — | 70,548 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta14`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta14.csv` | Phone CSV | 2,885 | S2 | 0 | 540,523 |
| `V-vta14.csv` | Vehicle CSV | 2,885 | S1 | 0 | 612,352 |
| `V-Vta14.JPG` | Route JPG | 448 × 636 | — | — | 59,948 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta15`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta15.csv` | Phone CSV | 833 | S2 | 0 | 156,907 |
| `V-vta15.csv` | Vehicle CSV | 833 | S1 | 0 | 175,132 |
| `V-Vta15.JPG` | Route JPG | 555 × 615 | — | — | 64,657 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta16`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta16.csv` | Phone CSV | 11,335 | S2 | 0 | 2,111,083 |
| `V-vta16.csv` | Vehicle CSV | 11,335 | S1 | 0 | 2,410,634 |
| `V-Vta16.JPG` | Route JPG | 488 × 636 | — | — | 73,109 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta17`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta17.csv` | Phone CSV | 4,519 | S2 | 0 | 839,635 |
| `V-vta17.csv` | Vehicle CSV | 4,519 | S1 | 0 | 972,437 |
| `V-Vta17.JPG` | Route JPG | 1065 × 629 | — | — | 118,853 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta19`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta19.csv` | Phone CSV | 292 | S2 | 0 | 54,578 |
| `V-vta19.csv` | Vehicle CSV | 292 | S1 | 0 | 61,675 |
| `V-Vta19.JPG` | Route JPG | 1084 × 565 | — | — | 117,786 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta20`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta20.csv` | Phone CSV | 3,223 | S2 | 0 | 582,891 |
| `V-vta20.csv` | Vehicle CSV | 3,223 | S1 | 0 | 596,090 |
| `V-Vta20.JPG` | Route JPG | 851 × 596 | — | — | 71,863 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta21`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta21.csv` | Phone CSV | 2,079 | S2 | 0 | 388,495 |
| `V-vta21.csv` | Vehicle CSV | 2,079 | S1 | 0 | 450,180 |
| `V-Vta21.JPG` | Route JPG | 906 × 629 | — | — | 83,580 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta22`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta22.csv` | Phone CSV | 1,564 | S2 | 0 | 290,331 |
| `V-vta22.csv` | Vehicle CSV | 1,564 | S1 | 0 | 338,739 |
| `V-Vta22.JPG` | Route JPG | 925 × 654 | — | — | 90,650 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta23`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta23.csv` | Phone CSV | 1,110 | S2 | 0 | 206,507 |
| `V-vta23.csv` | Vehicle CSV | 1,110 | S1 | 0 | 242,444 |
| `V-Vta23.JPG` | Route JPG | 1081 × 484 | — | — | 79,982 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta24`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta24.csv` | Phone CSV | 1,171 | S2 | 0 | 217,212 |
| `V-vta24.csv` | Vehicle CSV | 1,171 | S1 | 0 | 250,448 |
| `V-Vta24.JPG` | Route JPG | 1053 × 475 | — | — | 105,035 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta25`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta25.csv` | Phone CSV | 646 | S2 | 0 | 118,562 |
| `V-vta25.csv` | Vehicle CSV | 646 | S1 | 0 | 135,915 |
| `V-Vta25.JPG` | Route JPG | 1071 × 347 | — | — | 68,783 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta26`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta26.csv` | Phone CSV | 1,935 | S2 | 0 | 358,553 |
| `V-vta26.csv` | Vehicle CSV | 1,935 | S1 | 0 | 401,896 |
| `V-Vta26.JPG` | Route JPG | 383 × 663 | — | — | 43,055 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta27`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta27.csv` | Phone CSV | 2,540 | S2 | 0 | 471,023 |
| `V-vta27.csv` | Vehicle CSV | 2,540 | S1 | 0 | 550,395 |
| `V-Vta27.JPG` | Route JPG | 462 × 666 | — | — | 54,531 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta28`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta28.csv` | Phone CSV | 4,210 | S2 | 0 | 781,902 |
| `V-vta28.csv` | Vehicle CSV | 4,210 | S1 | 0 | 901,238 |
| `V-Vta28.JPG` | Route JPG | 1086 × 582 | — | — | 94,954 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta29`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta29.csv` | Phone CSV | 23,705 | S2 | 0 | 4,387,027 |
| `V-vta29.csv` | Vehicle CSV | 23,705 | S1 | 0 | 5,117,097 |
| `V-Vta29.JPG` | Route JPG | 566 × 635 | — | — | 80,481 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vta (Driver E)/Vta30`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vta30.csv` | Phone CSV | 17,136 | S2 | 0 | 3,175,640 |
| `V-vta30.csv` | Vehicle CSV | 17,136 | S1 | 0 | 3,628,928 |
| `V-Vta30.JPG` | Route JPG | 852 × 641 | — | — | 127,644 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb01`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb1.csv` | Phone CSV | 32,459 | S2 | 0 | 6,052,896 |
| `V-vtb1.csv` | Vehicle CSV | 32,459 | S1 | 0 | 6,989,783 |
| `V-Vtb1.JPG` | Route JPG | 1026 × 635 | — | — | 156,966 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb2.csv` | Phone CSV | 5,712 | S2 | 0 | 1,053,029 |
| `V-vtb2.csv` | Vehicle CSV | 5,712 | S1 | 0 | 1,200,565 |
| `V-Vtb2.JPG` | Route JPG | 1081 × 625 | — | — | 146,447 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb03`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb3.csv` | Phone CSV | 8,240 | S2 | 0 | 1,530,275 |
| `V-vtb3.csv` | Vehicle CSV | 8,240 | S1 | 0 | 1,739,502 |
| `V-Vtb3.JPG` | Route JPG | 1063 × 640 | — | — | 166,763 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb04`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb4.csv` | Phone CSV | 556 | S2 | 0 | 103,090 |
| `V-vtb4.csv` | Vehicle CSV | 556 | S1 | 0 | 118,374 |
| `V-Vtb4.JPG` | Route JPG | 1048 × 628 | — | — | 166,765 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb05`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb5.csv` | Phone CSV | 64,388 | S2 | 0 | 12,010,333 |
| `V-vtb5.csv` | Vehicle CSV | 64,388 | S1 | 0 | 13,567,208 |
| `V-Vtb5.JPG` | Route JPG | 523 × 632 | — | — | 96,900 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb06`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb6.csv` | Phone CSV | 498 | S2 | 0 | 94,210 |
| `V-vtb6.csv` | Vehicle CSV | 498 | S1 | 0 | 105,659 |
| `V-Vtb6.JPG` | Route JPG | 765 × 628 | — | — | 149,826 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb07`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb7.csv` | Phone CSV | 461 | S2 | 0 | 87,349 |
| `V-vtb7.csv` | Vehicle CSV | 461 | S1 | 0 | 101,086 |
| `V-Vtb7.JPG` | Route JPG | 813 × 559 | — | — | 112,096 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb08`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb8.csv` | Phone CSV | 668 | S2 | 0 | 126,023 |
| `V-vtb8.csv` | Vehicle CSV | 668 | S1 | 0 | 138,162 |
| `V-Vtb8.JPG` | Route JPG | 927 × 573 | — | — | 71,872 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb09`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb9.csv` | Phone CSV | 452 | S2 | 0 | 85,640 |
| `V-vtb9.csv` | Vehicle CSV | 452 | S1 | 0 | 93,354 |
| `V-Vtb9.JPG` | Route JPG | 956 × 592 | — | — | 85,590 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb10`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb10.csv` | Phone CSV | 196 | S2 | 0 | 37,176 |
| `V-vtb10.csv` | Vehicle CSV | 195 | S1 | 0 | 42,725 |
| `V-Vtb10.JPG` | Route JPG | 994 × 586 | — | — | 155,179 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb11`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb11.csv` | Phone CSV | 361 | S2 | 0 | 68,659 |
| `V-vtb11.csv` | Vehicle CSV | 361 | S1 | 0 | 74,838 |
| `V-Vtb11.JPG` | Route JPG | 1024 × 583 | — | — | 71,219 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vtb (Driver E)/Vtb12`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vtb12.csv` | Phone CSV | 447 | S2 | 0 | 83,892 |
| `V-vtb12.csv` | Vehicle CSV | 447 | S1 | 0 | 94,747 |
| `V-Vtb12.JPG` | Route JPG | 1055 × 616 | — | — | 155,651 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw01`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw1.csv` | Phone CSV | 20,476 | S2 | 0 | 3,524,952 |
| `V-Vw1.csv` | Vehicle CSV | 20,475 | S1 | 0 | 4,001,856 |
| `V-Vw1.JPG` | Route JPG | 874 × 634 | — | — | 73,282 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw2.csv` | Phone CSV | 52,713 | S2 | 0 | 9,883,172 |
| `V-Vw2.csv` | Vehicle CSV | 52,712 | S1 | 0 | 11,341,576 |
| `V-Vw2.JPG` | Route JPG | 748 × 624 | — | — | 125,623 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw03`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw3.csv` | Phone CSV | 3,861 | S2 | 0 | 720,455 |
| `V-Vw3.csv` | Vehicle CSV | 3,861 | S1 | 0 | 839,545 |
| `V-Vw3.JPG` | Route JPG | 718 × 641 | — | — | 156,856 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw04`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw4.csv` | Phone CSV | 126,526 | S2 | 0 | 23,607,418 |
| `V-Vw4.csv` | Vehicle CSV | 126,527 | S1 | 0 | 27,124,526 |
| `V-Vw4.JPG` | Route JPG | 1042 × 635 | — | — | 178,818 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw05`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw5.csv` | Phone CSV | 1,012 | S2 | 0 | 188,883 |
| `V-Vw5.csv` | Vehicle CSV | 1,012 | S1 | 0 | 216,316 |
| `V-Vw5.JPG` | Route JPG | 696 × 595 | — | — | 144,350 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw06`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw6.csv` | Phone CSV | 1,281 | S2 | 0 | 238,315 |
| `V-Vw6.csv` | Vehicle CSV | 1,281 | S1 | 0 | 278,191 |
| `V-Vw6.JPG` | Route JPG | 726 × 627 | — | — | 160,845 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw07`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw7.csv` | Phone CSV | 1,602 | S2 | 0 | 300,843 |
| `V-Vw7.csv` | Vehicle CSV | 1,602 | S1 | 0 | 346,895 |
| `V-Vw7.JPG` | Route JPG | 1069 × 506 | — | — | 180,212 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw08`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw8.csv` | Phone CSV | 1,529 | S2 | 0 | 287,123 |
| `V-Vw8.csv` | Vehicle CSV | 1,529 | S1 | 0 | 332,609 |
| `V-Vw8.JPG` | Route JPG | 1064 × 619 | — | — | 210,836 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw09`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw9.csv` | Phone CSV | 552 | S2 | 0 | 103,572 |
| `V-Vw9.csv` | Vehicle CSV | 553 | S1 | 0 | 121,383 |
| `V-Vw9.JPG` | Route JPG | 1071 × 422 | — | — | 156,747 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw10`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw10.csv` | Phone CSV | 652 | S2 | 0 | 123,092 |
| `V-Vw10.csv` | Vehicle CSV | 652 | S1 | 0 | 141,457 |
| `V-Vw10.JPG` | Route JPG | 1049 × 542 | — | — | 188,195 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw11`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw11.csv` | Phone CSV | 4,909 | S2 | 0 | 924,189 |
| `V-Vw11.csv` | Vehicle CSV | 4,909 | S1 | 0 | 1,032,515 |
| `V-Vw11.JPG` | Route JPG | 976 × 630 | — | — | 164,533 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw12`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw12.csv` | Phone CSV | 918 | S2 | 0 | 170,958 |
| `V-Vw12.csv` | Vehicle CSV | 918 | S1 | 0 | 188,273 |
| `V-Vw12.JPG` | Route JPG | 501 × 635 | — | — | 77,937 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw13`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw13.csv` | Phone CSV | 284 | S2 | 0 | 53,041 |
| `V-Vw13.csv` | Vehicle CSV | 284 | S1 | 0 | 59,207 |
| `V-Vw13.JPG` | Route JPG | 576 × 614 | — | — | 61,617 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw14a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw14a.csv` | Phone CSV | 3,138 | S2 | 0 | 585,872 |
| `V-Vw14a.csv` | Vehicle CSV | 3,138 | S1 | 0 | 651,054 |
| `V-Vw14a.JPG` | Route JPG | 477 × 643 | — | — | 81,078 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw14b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw14b.csv` | Phone CSV | 19,588 | S2 | 0 | 3,668,924 |
| `V-Vw14b.csv` | Vehicle CSV | 19,588 | S1 | 0 | 4,120,915 |
| `V-Vw14b.JPG` | Route JPG | 928 × 624 | — | — | 175,205 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw14c`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw14c.csv` | Phone CSV | 15,826 | S2 | 0 | 2,957,471 |
| `V-Vw14c.csv` | Vehicle CSV | 15,826 | S1 | 0 | 3,363,425 |
| `V-Vw14c.JPG` | Route JPG | 807 × 636 | — | — | 128,142 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw15`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw15.csv` | Phone CSV | 1,380 | S2 | 0 | 254,039 |
| `V-Vw15.csv` | Vehicle CSV | 1,391 | S1 | 0 | 263,885 |
| `V-Vw15.JPG` | Route JPG | 823 × 637 | — | — | 103,546 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw16a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw16a.csv` | Phone CSV | 5,879 | S2 | 0 | 1,100,323 |
| `V-Vw16a.csv` | Vehicle CSV | 5,879 | S1 | 0 | 1,241,037 |
| `V-Vw16a.JPG` | Route JPG | 1036 × 600 | — | — | 136,984 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw16b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw16b.csv` | Phone CSV | 1,126 | S2 | 0 | 211,892 |
| `V-Vw16b.csv` | Vehicle CSV | 1,126 | S1 | 0 | 239,979 |
| `V-Vw16b.JPG` | Route JPG | 981 × 641 | — | — | 95,228 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw17`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Vw17.csv` | Phone CSV | 329 | S2 | 0 | 62,489 |
| `V-Vw17.csv` | Vehicle CSV | 329 | S1 | 0 | 71,065 |
| `V-Vw17.JPG` | Route JPG | 1049 × 611 | — | — | 130,602 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Categorised IOVNB Dataset/Y (Driver D)/Y1`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-Y1.csv` | Phone CSV | 70,285 | S2 | 98 | 13,039,543 |
| `V-Y1.csv` | Vehicle CSV | 70,285 | S1 | 0 | 14,986,075 |
| `V-Y1.JPG` | Route JPG | 712 × 642 | — | — | 149,842 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Uncategorised IOVNB Dataset/S-Dataset`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-M.csv` | Phone CSV | 105,974 | S3 | 0 | 19,798,716 |
| `S-S1.csv` | Phone CSV | 51,746 | S3 | 0 | 10,011,984 |
| `S-S2.csv` | Phone CSV | 93,876 | S3 | 0 | 17,469,297 |
| `S-S3a.csv` | Phone CSV | 24,621 | S3 | 0 | 4,730,156 |
| `S-S3b.csv` | Phone CSV | 6,813 | S3 | 0 | 1,297,427 |
| `S-S3c.csv` | Phone CSV | 37,183 | S3 | 0 | 7,158,727 |
| `S-S4.csv` | Phone CSV | 94,600 | S3 | 0 | 17,574,509 |
| `S-Vfa01.csv` | Phone CSV | 11,486 | S5 | 0 | 2,134,661 |
| `S-Vfa02.csv` | Phone CSV | 67,523 | S5 | 0 | 12,603,651 |
| `S-Vta10.csv` | Phone CSV | 1,502 | S3 | 0 | 296,597 |
| `S-Vta11.csv` | Phone CSV | 510 | S3 | 0 | 99,409 |
| `S-Vta12.csv` | Phone CSV | 610 | S3 | 0 | 119,914 |
| `S-Vta13.csv` | Phone CSV | 404 | S3 | 0 | 79,167 |
| `S-Vta14.csv` | Phone CSV | 2,885 | S3 | 0 | 578,774 |
| `S-Vta15.csv` | Phone CSV | 833 | S3 | 0 | 166,282 |
| `S-Vta16.csv` | Phone CSV | 11,335 | S3 | 0 | 2,231,230 |
| `S-Vta17.csv` | Phone CSV | 4,519 | S3 | 0 | 897,277 |
| `S-Vta19.csv` | Phone CSV | 292 | S3 | 0 | 55,537 |
| `S-Vta1a.csv` | Phone CSV | 25,676 | S3 | 0 | 4,766,735 |
| `S-Vta1b.csv` | Phone CSV | 954 | S3 | 0 | 188,978 |
| `S-Vta2.csv` | Phone CSV | 10,991 | S3 | 0 | 2,149,518 |
| `S-Vta20.csv` | Phone CSV | 3,223 | S3 | 0 | 608,133 |
| `S-Vta21.csv` | Phone CSV | 2,079 | S3 | 0 | 414,878 |
| `S-Vta22.csv` | Phone CSV | 1,564 | S3 | 0 | 308,800 |
| `S-Vta23.csv` | Phone CSV | 1,110 | S3 | 0 | 222,406 |
| `S-Vta24.csv` | Phone CSV | 1,171 | S3 | 0 | 236,619 |
| `S-Vta25.csv` | Phone CSV | 646 | S3 | 0 | 127,720 |
| `S-Vta26.csv` | Phone CSV | 1,935 | S3 | 0 | 387,222 |
| `S-Vta27.csv` | Phone CSV | 2,540 | S3 | 0 | 502,320 |
| `S-Vta28.csv` | Phone CSV | 4,210 | S3 | 0 | 842,776 |
| `S-Vta29.csv` | Phone CSV | 23,705 | S3 | 0 | 4,387,022 |
| `S-Vta3.csv` | Phone CSV | 645 | S3 | 0 | 123,424 |
| `S-Vta30.csv` | Phone CSV | 17,136 | S3 | 0 | 3,175,635 |
| `S-Vta4.csv` | Phone CSV | 1,789 | S3 | 0 | 349,178 |
| `S-Vta5.csv` | Phone CSV | 307 | S3 | 0 | 60,433 |
| `S-Vta6.csv` | Phone CSV | 1,376 | S3 | 0 | 272,232 |
| `S-Vta7.csv` | Phone CSV | 840 | S3 | 0 | 164,330 |
| `S-Vta8.csv` | Phone CSV | 3,676 | S3 | 0 | 723,761 |
| `S-Vta9.csv` | Phone CSV | 156 | S3 | 0 | 31,642 |
| `S-Vtb1.csv` | Phone CSV | 32,459 | S3 | 0 | 6,052,891 |
| `S-Vtb10.csv` | Phone CSV | 196 | S3 | 0 | 38,686 |
| `S-Vtb11.csv` | Phone CSV | 361 | S3 | 0 | 70,204 |
| `S-Vtb12.csv` | Phone CSV | 447 | S3 | 0 | 87,659 |
| `S-Vtb2.csv` | Phone CSV | 5,712 | S3 | 0 | 1,053,024 |
| `S-Vtb3.csv` | Phone CSV | 8,240 | S3 | 0 | 1,530,270 |
| `S-Vtb4.csv` | Phone CSV | 556 | S3 | 0 | 111,008 |
| `S-Vtb5.csv` | Phone CSV | 64,388 | S3 | 0 | 12,612,030 |
| `S-Vtb6.csv` | Phone CSV | 498 | S3 | 0 | 99,549 |
| `S-Vtb7.csv` | Phone CSV | 461 | S3 | 0 | 90,646 |
| `S-Vtb8.csv` | Phone CSV | 668 | S3 | 0 | 131,319 |
| `S-Vtb9.csv` | Phone CSV | 452 | S3 | 0 | 89,626 |
| `S-Vw1.csv` | Phone CSV | 20,476 | S3 | 0 | 3,524,947 |
| `S-Vw10.csv` | Phone CSV | 652 | S3 | 0 | 129,358 |
| `S-Vw11.csv` | Phone CSV | 4,909 | S3 | 0 | 964,445 |
| `S-Vw12.csv` | Phone CSV | 918 | S3 | 0 | 176,321 |
| `S-Vw13.csv` | Phone CSV | 284 | S3 | 0 | 54,886 |
| `S-Vw14a.csv` | Phone CSV | 3,138 | S3 | 0 | 608,561 |
| `S-Vw14b.csv` | Phone CSV | 19,588 | S3 | 0 | 3,869,411 |
| `S-Vw14c.csv` | Phone CSV | 15,826 | S3 | 0 | 3,129,600 |
| `S-Vw15.csv` | Phone CSV | 1,380 | S3 | 0 | 268,621 |
| `S-Vw16a.csv` | Phone CSV | 5,879 | S3 | 0 | 1,152,501 |
| `S-Vw16b.csv` | Phone CSV | 1,126 | S3 | 0 | 221,088 |
| `S-Vw17.csv` | Phone CSV | 329 | S3 | 0 | 65,869 |
| `S-Vw2.csv` | Phone CSV | 52,713 | S3 | 0 | 9,883,167 |
| `S-Vw3.csv` | Phone CSV | 3,861 | S3 | 0 | 754,118 |
| `S-Vw4.csv` | Phone CSV | 126,526 | S3 | 0 | 23,607,413 |
| `S-Vw5.csv` | Phone CSV | 1,012 | S3 | 0 | 194,565 |
| `S-Vw6.csv` | Phone CSV | 1,281 | S3 | 0 | 246,923 |
| `S-Vw7.csv` | Phone CSV | 1,602 | S3 | 0 | 313,333 |
| `S-Vw8.csv` | Phone CSV | 1,529 | S3 | 0 | 297,380 |
| `S-Vw9.csv` | Phone CSV | 552 | S3 | 0 | 106,439 |
| `S-Y1.csv` | Phone CSV | 70,285 | S3 | 98 | 13,039,538 |

### `Synchronised V abd S datasets/Synchronised V abd S datasets/Uncategorised IOVNB Dataset/V-Dataset`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-M.csv` | Vehicle CSV | 105,974 | S1 | 0 | 22,507,823 |
| `V-S1.csv` | Vehicle CSV | 51,746 | S1 | 0 | 10,967,129 |
| `V-S2.csv` | Vehicle CSV | 93,876 | S1 | 0 | 20,091,681 |
| `V-S3a.csv` | Vehicle CSV | 24,621 | S1 | 0 | 5,286,764 |
| `V-S3b.csv` | Vehicle CSV | 6,813 | S1 | 0 | 1,464,196 |
| `V-S3c.csv` | Vehicle CSV | 37,183 | S1 | 0 | 7,976,092 |
| `V-S4.csv` | Vehicle CSV | 94,600 | S1 | 0 | 20,164,189 |
| `V-Vfa01.csv` | Vehicle CSV | 11,535 | S1 | 0 | 2,398,099 |
| `V-Vfa02.csv` | Vehicle CSV | 67,755 | S1 | 0 | 13,955,001 |
| `V-vta10.csv` | Vehicle CSV | 1,502 | S1 | 0 | 317,921 |
| `V-vta11.csv` | Vehicle CSV | 510 | S1 | 0 | 111,690 |
| `V-vta12.csv` | Vehicle CSV | 610 | S1 | 0 | 128,904 |
| `V-vta13.csv` | Vehicle CSV | 404 | S1 | 0 | 86,963 |
| `V-vta14.csv` | Vehicle CSV | 2,885 | S1 | 0 | 612,352 |
| `V-vta15.csv` | Vehicle CSV | 833 | S1 | 0 | 175,132 |
| `V-vta16.csv` | Vehicle CSV | 11,335 | S1 | 0 | 2,410,634 |
| `V-vta17.csv` | Vehicle CSV | 4,519 | S1 | 0 | 972,437 |
| `V-vta19.csv` | Vehicle CSV | 292 | S1 | 0 | 61,675 |
| `V-Vta1a.csv` | Vehicle CSV | 25,676 | S1 | 0 | 5,444,513 |
| `V-Vta1b.csv` | Vehicle CSV | 953 | S1 | 0 | 205,277 |
| `V-vta2.csv` | Vehicle CSV | 10,991 | S1 | 0 | 2,307,461 |
| `V-vta20.csv` | Vehicle CSV | 3,223 | S1 | 0 | 596,090 |
| `V-vta21.csv` | Vehicle CSV | 2,079 | S1 | 0 | 450,180 |
| `V-vta22.csv` | Vehicle CSV | 1,564 | S1 | 0 | 338,739 |
| `V-vta23.csv` | Vehicle CSV | 1,110 | S1 | 0 | 242,444 |
| `V-vta24.csv` | Vehicle CSV | 1,171 | S1 | 0 | 250,448 |
| `V-vta25.csv` | Vehicle CSV | 646 | S1 | 0 | 135,915 |
| `V-vta26.csv` | Vehicle CSV | 1,935 | S1 | 0 | 401,896 |
| `V-vta27.csv` | Vehicle CSV | 2,540 | S1 | 0 | 550,395 |
| `V-vta28.csv` | Vehicle CSV | 4,210 | S1 | 0 | 901,238 |
| `V-vta29.csv` | Vehicle CSV | 23,705 | S1 | 0 | 5,117,097 |
| `V-vta3.csv` | Vehicle CSV | 645 | S1 | 0 | 137,891 |
| `V-vta30.csv` | Vehicle CSV | 17,136 | S1 | 0 | 3,628,928 |
| `V-vta4.csv` | Vehicle CSV | 1,789 | S1 | 0 | 380,874 |
| `V-vta5.csv` | Vehicle CSV | 307 | S1 | 0 | 66,401 |
| `V-vta6.csv` | Vehicle CSV | 1,376 | S1 | 0 | 289,249 |
| `V-vta7.csv` | Vehicle CSV | 840 | S1 | 0 | 179,784 |
| `V-vta8.csv` | Vehicle CSV | 3,676 | S1 | 0 | 753,939 |
| `V-vta9.csv` | Vehicle CSV | 156 | S1 | 0 | 33,110 |
| `V-vtb1.csv` | Vehicle CSV | 32,459 | S1 | 0 | 6,989,783 |
| `V-vtb10.csv` | Vehicle CSV | 195 | S1 | 0 | 42,725 |
| `V-vtb11.csv` | Vehicle CSV | 361 | S1 | 0 | 74,838 |
| `V-vtb12.csv` | Vehicle CSV | 447 | S1 | 0 | 94,747 |
| `V-vtb2.csv` | Vehicle CSV | 5,712 | S1 | 0 | 1,200,565 |
| `V-vtb3.csv` | Vehicle CSV | 8,240 | S1 | 0 | 1,739,502 |
| `V-vtb4.csv` | Vehicle CSV | 556 | S1 | 0 | 118,374 |
| `V-vtb5.csv` | Vehicle CSV | 64,388 | S1 | 0 | 13,567,208 |
| `V-vtb6.csv` | Vehicle CSV | 498 | S1 | 0 | 105,659 |
| `V-vtb7.csv` | Vehicle CSV | 461 | S1 | 0 | 101,086 |
| `V-vtb8.csv` | Vehicle CSV | 668 | S1 | 0 | 138,162 |
| `V-vtb9.csv` | Vehicle CSV | 452 | S1 | 0 | 93,354 |
| `V-Vw1.csv` | Vehicle CSV | 20,475 | S1 | 0 | 4,001,856 |
| `V-Vw10.csv` | Vehicle CSV | 652 | S1 | 0 | 141,457 |
| `V-Vw11.csv` | Vehicle CSV | 4,909 | S1 | 0 | 1,032,515 |
| `V-Vw12.csv` | Vehicle CSV | 918 | S1 | 0 | 188,273 |
| `V-Vw13.csv` | Vehicle CSV | 284 | S1 | 0 | 59,207 |
| `V-Vw14a.csv` | Vehicle CSV | 3,138 | S1 | 0 | 651,054 |
| `V-Vw14b.csv` | Vehicle CSV | 19,588 | S1 | 0 | 4,120,915 |
| `V-Vw14c.csv` | Vehicle CSV | 15,826 | S1 | 0 | 3,363,425 |
| `V-Vw15.csv` | Vehicle CSV | 1,391 | S1 | 0 | 263,885 |
| `V-Vw16a.csv` | Vehicle CSV | 5,879 | S1 | 0 | 1,241,037 |
| `V-Vw16b.csv` | Vehicle CSV | 1,126 | S1 | 0 | 239,979 |
| `V-Vw17.csv` | Vehicle CSV | 329 | S1 | 0 | 71,065 |
| `V-Vw2.csv` | Vehicle CSV | 52,712 | S1 | 0 | 11,341,576 |
| `V-Vw3.csv` | Vehicle CSV | 3,861 | S1 | 0 | 839,545 |
| `V-Vw4.csv` | Vehicle CSV | 126,527 | S1 | 0 | 27,124,526 |
| `V-Vw5.csv` | Vehicle CSV | 1,012 | S1 | 0 | 216,316 |
| `V-Vw6.csv` | Vehicle CSV | 1,281 | S1 | 0 | 278,191 |
| `V-Vw7.csv` | Vehicle CSV | 1,602 | S1 | 0 | 346,895 |
| `V-Vw8.csv` | Vehicle CSV | 1,529 | S1 | 0 | 332,609 |
| `V-Vw9.csv` | Vehicle CSV | 553 | S1 | 0 | 121,383 |
| `V-Y1.csv` | Vehicle CSV | 70,285 | S1 | 0 | 14,986,075 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/M (Driver B)`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-M.csv` | Vehicle CSV | 105,995 | S1 | 0 | 21,659,868 |
| `V-M.JPG` | Route JPG | 741 × 611 | — | — | 132,217 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/S (Driver A)/S1`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-S1.csv` | Vehicle CSV | 51,790 | S1 | 0 | 10,505,959 |
| `V-S1.JPG` | Route JPG | 1088 × 580 | — | — | 207,995 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/S (Driver A)/S2`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-S2.csv` | Vehicle CSV | 93,900 | S1 | 0 | 19,297,256 |
| `V-S2.JPG` | Route JPG | 847 × 634 | — | — | 133,093 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/S (Driver A)/S3a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-S3a.csv` | Vehicle CSV | 24,660 | S1 | 0 | 5,089,354 |
| `V-S3a.JPG` | Route JPG | 1087 × 621 | — | — | 169,114 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/S (Driver A)/S3b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-S3b.csv` | Vehicle CSV | 6,840 | S1 | 0 | 1,410,120 |
| `V-S3b.JPG` | Route JPG | 555 × 610 | — | — | 132,557 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/S (Driver A)/S3c`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-S3c.csv` | Vehicle CSV | 37,220 | S1 | 0 | 7,687,239 |
| `V-S3c.JPG` | Route JPG | 856 × 649 | — | — | 141,869 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/S (Driver A)/S4`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-S4.csv` | Vehicle CSV | 97,824 | S1 | 0 | 19,863,006 |
| `V-S4.JPG` | Route JPG | 602 × 632 | — | — | 123,854 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/St (Driver C)/St1`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-St1.csv` | Vehicle CSV | 57,213 | S1 | 0 | 11,545,416 |
| `V-St1.JPG` | Route JPG | 929 × 656 | — | — | 194,298 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/St (Driver C)/St4`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-St4.csv` | Vehicle CSV | 13,591 | S1 | 0 | 2,794,203 |
| `V-St4.JPG` | Route JPG | 799 × 657 | — | — | 136,825 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/St (Driver C)/St6`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-St6.csv` | Vehicle CSV | 51,360 | S1 | 0 | 10,437,990 |
| `V-St6.JPG` | Route JPG | 342 × 650 | — | — | 60,353 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/St (Driver C)/St7`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-St7.csv` | Vehicle CSV | 44,427 | S1 | 0 | 8,944,996 |
| `V-St7.JPG` | Route JPG | 719 × 605 | — | — | 112,361 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfa01`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfa01.csv` | Vehicle CSV | 11,535 | S1 | 0 | 2,398,099 |
| `V-Vfa01.JPG` | Route JPG | 837 × 637 | — | — | 103,673 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfa02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfa02.csv` | Vehicle CSV | 67,755 | S1 | 0 | 13,955,001 |
| `V-Vfa02.JPG` | Route JPG | 603 × 653 | — | — | 103,932 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb01a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb01a.csv` | Vehicle CSV | 17,000 | S1 | 0 | 3,363,089 |
| `V-Vfb01a.JPG` | Route JPG | 570 × 666 | — | — | 135,657 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb01b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb01b.csv` | Vehicle CSV | 3,880 | S1 | 0 | 795,266 |
| `V-Vfb01b.JPG` | Route JPG | 607 × 635 | — | — | 110,745 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb01c`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb01c.csv` | Vehicle CSV | 6,320 | S1 | 0 | 1,280,169 |
| `V-Vfb01c.JPG` | Route JPG | 1093 × 535 | — | — | 166,245 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb01d`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb01d.csv` | Vehicle CSV | 10,713 | S1 | 0 | 2,123,447 |
| `V-Vfb01d.JPG` | Route JPG | 1037 × 611 | — | — | 170,985 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb02a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb02a.csv` | Vehicle CSV | 35,960 | S1 | 0 | 7,418,599 |
| `V-Vfb02a.JPG` | Route JPG | 662 × 640 | — | — | 106,655 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb02b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb02b.csv` | Vehicle CSV | 11,000 | S1 | 0 | 2,240,834 |
| `V-Vfb02b.JPG` | Route JPG | 1064 × 648 | — | — | 206,869 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb02c`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb02c.csv` | Vehicle CSV | 640 | S1 | 0 | 132,991 |
| `V-Vfb02c.JPG` | Route JPG | 999 × 615 | — | — | 157,317 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb02d`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb02d.csv` | Vehicle CSV | 880 | S1 | 0 | 182,339 |
| `V-Vfb02d.JPG` | Route JPG | 672 × 600 | — | — | 127,100 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb02e`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb02e.csv` | Vehicle CSV | 980 | S1 | 0 | 202,703 |
| `V-Vfb02e.JPG` | Route JPG | 594 × 613 | — | — | 100,923 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb02f`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb02f.csv` | Vehicle CSV | 660 | S1 | 0 | 136,684 |
| `V-Vfb02f.JPG` | Route JPG | 847 × 608 | — | — | 129,130 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vf (Driver E)/V-Vfb02g`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb02g.csv` | Vehicle CSV | 27,159 | S1 | 0 | 5,570,770 |
| `V-Vfb02g.JPG` | Route JPG | 650 × 640 | — | — | 112,560 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta01a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta1a.csv` | Vehicle CSV | 25,821 | S1 | 0 | 5,288,733 |
| `V-Vta1a.JPG` | Route JPG | 721 × 648 | — | — | 125,542 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta01b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vfb01b.JPG` | Route JPG | 607 × 635 | — | — | 110,745 |
| `V-Vta1b.csv` | Vehicle CSV | 956 | S1 | 0 | 198,110 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta2.csv` | Vehicle CSV | 10,995 | S1 | 0 | 2,222,734 |
| `V-Vta2.JPG` | Route JPG | 715 × 667 | — | — | 137,726 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta03`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta3.csv` | Vehicle CSV | 875 | S1 | 0 | 175,163 |
| `V-Vta3.JPG` | Route JPG | 1083 × 457 | — | — | 138,187 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta04`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta4.csv` | Vehicle CSV | 1,809 | S1 | 0 | 370,003 |
| `V-Vta4.JPG` | Route JPG | 575 × 603 | — | — | 124,092 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta05`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta5.csv` | Vehicle CSV | 357 | S1 | 0 | 73,728 |
| `V-Vta5.JPG` | Route JPG | 703 × 627 | — | — | 115,310 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta06`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta6.csv` | Vehicle CSV | 1,393 | S1 | 0 | 284,633 |
| `V-Vta6.JPG` | Route JPG | 1090 × 409 | — | — | 86,806 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta07`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta7.csv` | Vehicle CSV | 857 | S1 | 0 | 176,565 |
| `V-Vta7.JPG` | Route JPG | 602 × 607 | — | — | 90,532 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta08`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta8.csv` | Vehicle CSV | 3,697 | S1 | 0 | 732,865 |
| `V-Vta8.JPG` | Route JPG | 612 × 668 | — | — | 93,238 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta09`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta9.csv` | Vehicle CSV | 226 | S1 | 0 | 46,738 |
| `V-Vta9.JPG` | Route JPG | 1087 × 552 | — | — | 128,689 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta10`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta10.csv` | Vehicle CSV | 1,570 | S1 | 0 | 321,356 |
| `V-Vta10.JPG` | Route JPG | 862 × 642 | — | — | 103,718 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta11`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta11.csv` | Vehicle CSV | 589 | S1 | 0 | 122,161 |
| `V-Vta11.JPG` | Route JPG | 700 × 601 | — | — | 50,368 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta12`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta12.csv` | Vehicle CSV | 690 | S1 | 0 | 140,652 |
| `V-Vta12.JPG` | Route JPG | 640 × 626 | — | — | 54,434 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta13`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta13.csv` | Vehicle CSV | 473 | S1 | 0 | 98,450 |
| `V-Vta13.JPG` | Route JPG | 669 × 590 | — | — | 70,548 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta14`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta14.csv` | Vehicle CSV | 2,893 | S1 | 0 | 593,318 |
| `V-Vta14.JPG` | Route JPG | 448 × 636 | — | — | 59,948 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta15`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta15.csv` | Vehicle CSV | 869 | S1 | 0 | 177,465 |
| `V-Vta15.JPG` | Route JPG | 555 × 615 | — | — | 64,657 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta16`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta16.csv` | Vehicle CSV | 11,361 | S1 | 0 | 2,312,817 |
| `V-Vta16.JPG` | Route JPG | 488 × 636 | — | — | 73,109 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta17`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta17.csv` | Vehicle CSV | 4,594 | S1 | 0 | 944,997 |
| `V-Vta17.JPG` | Route JPG | 1065 × 629 | — | — | 118,853 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta19`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta19.csv` | Vehicle CSV | 310 | S1 | 0 | 62,292 |
| `V-Vta19.JPG` | Route JPG | 1084 × 565 | — | — | 117,786 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta20`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta20.csv` | Vehicle CSV | 3,223 | S1 | 0 | 577,317 |
| `V-Vta20.JPG` | Route JPG | 851 × 596 | — | — | 71,863 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta21`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta21.csv` | Vehicle CSV | 2,088 | S1 | 0 | 430,922 |
| `V-Vta21.JPG` | Route JPG | 906 × 629 | — | — | 83,580 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta22`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta22.csv` | Vehicle CSV | 1,572 | S1 | 0 | 323,518 |
| `V-Vta22.JPG` | Route JPG | 925 × 654 | — | — | 90,650 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta23`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta23.csv` | Vehicle CSV | 1,119 | S1 | 0 | 232,810 |
| `V-Vta23.JPG` | Route JPG | 1081 × 484 | — | — | 79,982 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta24`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta24.csv` | Vehicle CSV | 1,184 | S1 | 0 | 241,654 |
| `V-Vta24.JPG` | Route JPG | 1053 × 475 | — | — | 105,035 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta25`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta25.csv` | Vehicle CSV | 646 | S1 | 0 | 129,385 |
| `V-Vta25.JPG` | Route JPG | 1071 × 347 | — | — | 68,783 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta26`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta26.csv` | Vehicle CSV | 1,947 | S1 | 0 | 388,954 |
| `V-Vta26.JPG` | Route JPG | 383 × 663 | — | — | 43,055 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta27`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta27.csv` | Vehicle CSV | 2,853 | S1 | 0 | 583,915 |
| `V-Vta27.JPG` | Route JPG | 462 × 666 | — | — | 54,531 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta28`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta28.csv` | Vehicle CSV | 4,219 | S1 | 0 | 859,662 |
| `V-Vta28.JPG` | Route JPG | 1086 × 582 | — | — | 94,954 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta29`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta29.csv` | Vehicle CSV | 23,737 | S1 | 0 | 4,907,770 |
| `V-Vta29.JPG` | Route JPG | 566 × 635 | — | — | 80,481 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vta (Driver E)/Vta30`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vta30.csv` | Vehicle CSV | 17,179 | S1 | 0 | 3,460,420 |
| `V-Vta30.JPG` | Route JPG | 852 × 641 | — | — | 127,644 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb01`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb1.csv` | Vehicle CSV | 32,459 | S1 | 0 | 6,696,680 |
| `V-Vtb1.JPG` | Route JPG | 1026 × 635 | — | — | 156,966 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb2.csv` | Vehicle CSV | 5,712 | S1 | 0 | 1,149,458 |
| `V-Vtb2.JPG` | Route JPG | 1081 × 625 | — | — | 146,447 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb03`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb3.csv` | Vehicle CSV | 8,289 | S1 | 0 | 1,663,807 |
| `V-Vtb3.JPG` | Route JPG | 1063 × 640 | — | — | 166,763 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb04`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb4.csv` | Vehicle CSV | 625 | S1 | 0 | 127,079 |
| `V-Vtb4.JPG` | Route JPG | 1048 × 628 | — | — | 166,765 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb05`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb5.csv` | Vehicle CSV | 64,610 | S1 | 0 | 13,070,303 |
| `V-Vtb5.JPG` | Route JPG | 523 × 632 | — | — | 96,900 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb06`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb6.csv` | Vehicle CSV | 508 | S1 | 0 | 104,997 |
| `V-Vtb6.JPG` | Route JPG | 765 × 628 | — | — | 149,826 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb07`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb7.csv` | Vehicle CSV | 461 | S1 | 0 | 94,550 |
| `V-Vtb7.JPG` | Route JPG | 813 × 559 | — | — | 112,096 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb08`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb8.csv` | Vehicle CSV | 699 | S1 | 0 | 138,144 |
| `V-Vtb8.JPG` | Route JPG | 927 × 573 | — | — | 71,872 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb09`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb9.csv` | Vehicle CSV | 457 | S1 | 0 | 92,473 |
| `V-Vtb9.JPG` | Route JPG | 956 × 592 | — | — | 85,590 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb10`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb10.csv` | Vehicle CSV | 195 | S1 | 0 | 40,687 |
| `V-Vtb10.JPG` | Route JPG | 994 × 586 | — | — | 155,179 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb11`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb11.csv` | Vehicle CSV | 433 | S1 | 0 | 88,068 |
| `V-Vtb11.JPG` | Route JPG | 1024 × 583 | — | — | 71,219 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb12`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb12.csv` | Vehicle CSV | 490 | S1 | 0 | 98,988 |
| `V-Vtb12.JPG` | Route JPG | 1055 × 616 | — | — | 155,651 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vtb (Driver E)/Vtb13`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vtb13.csv` | Vehicle CSV | 1,245 | S1 | 0 | 256,729 |
| `V-Vtb13.JPG` | Route JPG | 649 × 638 | — | — | 98,395 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw01`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw1.csv` | Vehicle CSV | 20,475 | S1 | 0 | 3,923,291 |
| `V-Vw1.JPG` | Route JPG | 874 × 634 | — | — | 73,282 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw02`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw2.csv` | Vehicle CSV | 52,712 | S1 | 0 | 10,887,065 |
| `V-Vw2.JPG` | Route JPG | 748 × 624 | — | — | 125,623 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw03`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw3.csv` | Vehicle CSV | 3,941 | S1 | 0 | 821,795 |
| `V-Vw3.JPG` | Route JPG | 718 × 641 | — | — | 156,856 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw04`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw4.csv` | Vehicle CSV | 126,573 | S1 | 0 | 26,069,987 |
| `V-Vw4.JPG` | Route JPG | 1042 × 635 | — | — | 178,818 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw05`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw5.csv` | Vehicle CSV | 1,050 | S1 | 0 | 215,664 |
| `V-Vw5.JPG` | Route JPG | 696 × 595 | — | — | 144,350 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw06`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw6.csv` | Vehicle CSV | 1,288 | S1 | 0 | 269,988 |
| `V-Vw6.JPG` | Route JPG | 726 × 627 | — | — | 160,845 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw07`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw7.csv` | Vehicle CSV | 1,689 | S1 | 0 | 350,184 |
| `V-Vw7.JPG` | Route JPG | 1069 × 506 | — | — | 180,212 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw08`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw8.csv` | Vehicle CSV | 1,599 | S1 | 0 | 332,898 |
| `V-Vw8.JPG` | Route JPG | 1064 × 619 | — | — | 210,836 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw09`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw9.csv` | Vehicle CSV | 601 | S1 | 0 | 125,970 |
| `V-Vw9.JPG` | Route JPG | 1071 × 422 | — | — | 156,747 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw10`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw10.csv` | Vehicle CSV | 670 | S1 | 0 | 138,464 |
| `V-Vw10.JPG` | Route JPG | 1049 × 542 | — | — | 188,195 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw11`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw10.csv` | Vehicle CSV | 670 | S1 | 0 | 138,464 |
| `V-Vw11.JPG` | Route JPG | 976 × 630 | — | — | 164,533 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw12`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw12.csv` | Vehicle CSV | 1,069 | S1 | 0 | 212,441 |
| `V-Vw12.JPG` | Route JPG | 501 × 635 | — | — | 77,937 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw13`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw13.csv` | Vehicle CSV | 297 | S1 | 0 | 58,854 |
| `V-Vw13.JPG` | Route JPG | 576 × 614 | — | — | 61,617 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw14a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw14a.csv` | Vehicle CSV | 3,140 | S1 | 0 | 627,655 |
| `V-Vw14a.JPG` | Route JPG | 477 × 643 | — | — | 81,078 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw14b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw14b.csv` | Vehicle CSV | 19,600 | S1 | 0 | 3,987,718 |
| `V-Vw14b.JPG` | Route JPG | 928 × 624 | — | — | 175,205 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw14c`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw14c.csv` | Vehicle CSV | 15,857 | S1 | 0 | 3,237,111 |
| `V-Vw14c.JPG` | Route JPG | 807 × 636 | — | — | 128,142 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw15`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw15.csv` | Vehicle CSV | 1,391 | S1 | 0 | 253,875 |
| `V-Vw15.JPG` | Route JPG | 823 × 637 | — | — | 103,546 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw16a`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw16a.csv` | Vehicle CSV | 6,000 | S1 | 0 | 1,209,828 |
| `V-Vw16a.JPG` | Route JPG | 1036 × 600 | — | — | 136,984 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw16b`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw16b.csv` | Vehicle CSV | 1,171 | S1 | 0 | 236,875 |
| `V-Vw16b.JPG` | Route JPG | 981 × 641 | — | — | 95,228 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Vw (Driver E)/Vw17`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Vw17.csv` | Vehicle CSV | 329 | S1 | 0 | 68,566 |
| `V-Vw17.JPG` | Route JPG | 1049 × 611 | — | — | 130,602 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Y (Driver D)/Y1`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Y1.csv` | Vehicle CSV | 70,341 | S1 | 0 | 14,394,860 |
| `V-Y1.JPG` | Route JPG | 712 × 642 | — | — | 149,842 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Categorised IOVNB (V) Dataset/V Dataset/Y (Driver D)/Y2`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-Y2.csv` | Vehicle CSV | 57,213 | S1 | 0 | 11,546,741 |
| `V-Y2.JPG` | Route JPG | 1005 × 581 | — | — | 184,094 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Uncategorised IOVNB (V and S) Dataset/S-Dataset`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `S-A1.csv` | Phone CSV | 5,942 | S2 | 0 | 1,072,488 |
| `S-A10.csv` | Phone CSV | 8,886 | S2 | 0 | 1,677,197 |
| `S-A11.csv` | Phone CSV | 5,155 | S2 | 0 | 926,919 |
| `S-A12.csv` | Phone CSV | 4,673 | S2 | 0 | 830,964 |
| `S-A13.csv` | Phone CSV | 9,184 | S2 | 0 | 1,654,726 |
| `S-A2.csv` | Phone CSV | 11,630 | S2 | 0 | 2,114,097 |
| `S-A3.csv` | Phone CSV | 11,132 | S2 | 0 | 2,003,758 |
| `S-A4.csv` | Phone CSV | 32,829 | S6 | 32,829 | 5,884,413 |
| `S-A5.csv` | Phone CSV | 85,041 | S2 | 700 | 15,172,267 |
| `S-A6.csv` | Phone CSV | 86,034 | S2 | 1,820 | 15,372,302 |
| `S-A7.csv` | Phone CSV | 43,872 | S2 | 0 | 7,790,641 |
| `S-A8.csv` | Phone CSV | 66,617 | S2 | 0 | 11,875,802 |
| `S-A9.csv` | Phone CSV | 11,962 | S2 | 0 | 2,260,778 |
| `S-I.csv` | Phone CSV | 5,800 | S2 | 0 | 983,096 |
| `S-M.csv` | Phone CSV | 105,974 | S2 | 0 | 19,798,721 |
| `S-S1.csv` | Phone CSV | 51,746 | S2 | 0 | 9,631,499 |
| `S-S2.csv` | Phone CSV | 93,876 | S2 | 0 | 17,469,302 |
| `S-S3a.csv` | Phone CSV | 24,621 | S2 | 0 | 4,580,130 |
| `S-S3b.csv` | Phone CSV | 6,813 | S3 | 0 | 1,297,427 |
| `S-S3c.csv` | Phone CSV | 37,183 | S2 | 0 | 6,881,631 |
| `S-S4.csv` | Phone CSV | 94,600 | S2 | 0 | 17,574,514 |
| `S-T1.csv` | Phone CSV | 25,759 | S4 | 0 | 3,801,675 |
| `S-T10.csv` | Phone CSV | 6,699 | S2 | 0 | 1,221,658 |
| `S-T11.csv` | Phone CSV | 5,690 | S2 | 0 | 1,030,228 |
| `S-T2.csv` | Phone CSV | 75,555 | S4 | 0 | 11,342,719 |
| `S-T3.csv` | Phone CSV | 65,859 | S4 | 0 | 9,838,523 |
| `S-T4.csv` | Phone CSV | 73,482 | S4 | 0 | 11,029,809 |
| `S-T5.csv` | Phone CSV | 46,387 | S4 | 0 | 7,021,030 |
| `S-T6.csv` | Phone CSV | 86,440 | S4 | 0 | 12,912,624 |
| `S-T7.csv` | Phone CSV | 101,690 | S4 | 0 | 15,381,654 |
| `S-T8.csv` | Phone CSV | 48,344 | S4 | 0 | 7,229,081 |
| `S-T9.csv` | Phone CSV | 79,909 | S4 | 0 | 11,946,986 |
| `S-Vfa01.csv` | Phone CSV | 11,486 | S2 | 0 | 2,134,667 |
| `S-Vfa02.csv` | Phone CSV | 67,523 | S2 | 0 | 12,603,657 |
| `S-Vta10.csv` | Phone CSV | 1,502 | S2 | 0 | 279,232 |
| `S-Vta11.csv` | Phone CSV | 510 | S2 | 0 | 95,272 |
| `S-Vta12.csv` | Phone CSV | 610 | S2 | 0 | 114,418 |
| `S-Vta13.csv` | Phone CSV | 404 | S2 | 0 | 76,217 |
| `S-Vta14.csv` | Phone CSV | 2,885 | S2 | 0 | 540,523 |
| `S-Vta15.csv` | Phone CSV | 833 | S2 | 0 | 156,907 |
| `S-Vta16.csv` | Phone CSV | 11,335 | S2 | 0 | 2,111,083 |
| `S-Vta17.csv` | Phone CSV | 4,519 | S2 | 0 | 839,635 |
| `S-Vta19.csv` | Phone CSV | 292 | S2 | 0 | 54,578 |
| `S-Vta1a.csv` | Phone CSV | 25,676 | S2 | 0 | 4,766,740 |
| `S-Vta1b.csv` | Phone CSV | 954 | S2 | 0 | 178,260 |
| `S-Vta2.csv` | Phone CSV | 10,991 | S2 | 0 | 2,038,713 |
| `S-Vta20.csv` | Phone CSV | 3,223 | S2 | 0 | 582,891 |
| `S-Vta21.csv` | Phone CSV | 2,079 | S2 | 0 | 388,495 |
| `S-Vta22.csv` | Phone CSV | 1,564 | S2 | 0 | 290,331 |
| `S-Vta23.csv` | Phone CSV | 1,110 | S2 | 0 | 206,507 |
| `S-Vta24.csv` | Phone CSV | 1,171 | S2 | 0 | 217,212 |
| `S-Vta25.csv` | Phone CSV | 646 | S2 | 0 | 118,562 |
| `S-Vta26.csv` | Phone CSV | 1,935 | S2 | 0 | 358,553 |
| `S-Vta27.csv` | Phone CSV | 2,540 | S2 | 0 | 471,023 |
| `S-Vta28.csv` | Phone CSV | 4,210 | S2 | 0 | 781,902 |
| `S-Vta29.csv` | Phone CSV | 23,705 | S2 | 0 | 4,387,027 |
| `S-Vta3.csv` | Phone CSV | 645 | S2 | 0 | 116,809 |
| `S-Vta30.csv` | Phone CSV | 17,136 | S2 | 0 | 3,175,640 |
| `S-Vta4.csv` | Phone CSV | 1,789 | S2 | 0 | 331,302 |
| `S-Vta5.csv` | Phone CSV | 307 | S2 | 0 | 57,485 |
| `S-Vta6.csv` | Phone CSV | 1,376 | S2 | 0 | 254,665 |
| `S-Vta7.csv` | Phone CSV | 840 | S2 | 0 | 155,360 |
| `S-Vta8.csv` | Phone CSV | 3,676 | S2 | 0 | 678,900 |
| `S-Vta9.csv` | Phone CSV | 156 | S2 | 0 | 29,554 |
| `S-Vtb1.csv` | Phone CSV | 32,459 | S2 | 0 | 6,052,896 |
| `S-Vtb10.csv` | Phone CSV | 196 | S2 | 0 | 37,176 |
| `S-Vtb11.csv` | Phone CSV | 361 | S2 | 0 | 68,659 |
| `S-Vtb12.csv` | Phone CSV | 447 | S2 | 0 | 83,892 |
| `S-Vtb2.csv` | Phone CSV | 5,712 | S2 | 0 | 1,053,029 |
| `S-Vtb3.csv` | Phone CSV | 8,240 | S2 | 0 | 1,530,275 |
| `S-Vtb4.csv` | Phone CSV | 556 | S2 | 0 | 103,090 |
| `S-Vtb5.csv` | Phone CSV | 64,388 | S2 | 0 | 12,010,333 |
| `S-Vtb6.csv` | Phone CSV | 498 | S2 | 0 | 94,210 |
| `S-Vtb7.csv` | Phone CSV | 461 | S2 | 0 | 87,349 |
| `S-Vtb8.csv` | Phone CSV | 668 | S2 | 0 | 126,023 |
| `S-Vtb9.csv` | Phone CSV | 452 | S2 | 0 | 85,640 |
| `S-Vw1.csv` | Phone CSV | 20,476 | S2 | 0 | 3,524,952 |
| `S-Vw10.csv` | Phone CSV | 652 | S2 | 0 | 123,092 |
| `S-Vw11.csv` | Phone CSV | 4,909 | S2 | 0 | 924,189 |
| `S-Vw12.csv` | Phone CSV | 918 | S2 | 0 | 170,958 |
| `S-Vw13.csv` | Phone CSV | 284 | S2 | 0 | 53,041 |
| `S-Vw14a.csv` | Phone CSV | 3,138 | S2 | 0 | 585,872 |
| `S-Vw14b.csv` | Phone CSV | 19,588 | S2 | 0 | 3,668,924 |
| `S-Vw14c.csv` | Phone CSV | 15,826 | S2 | 0 | 2,957,471 |
| `S-Vw15.csv` | Phone CSV | 1,380 | S2 | 0 | 254,039 |
| `S-Vw16a.csv` | Phone CSV | 5,879 | S2 | 0 | 1,100,323 |
| `S-Vw16b.csv` | Phone CSV | 1,126 | S2 | 0 | 211,892 |
| `S-Vw17.csv` | Phone CSV | 329 | S2 | 0 | 62,489 |
| `S-Vw2.csv` | Phone CSV | 52,713 | S2 | 0 | 9,883,172 |
| `S-Vw3.csv` | Phone CSV | 3,861 | S2 | 0 | 720,455 |
| `S-Vw4.csv` | Phone CSV | 126,526 | S2 | 0 | 23,607,418 |
| `S-Vw5.csv` | Phone CSV | 1,012 | S2 | 0 | 188,883 |
| `S-Vw6.csv` | Phone CSV | 1,281 | S2 | 0 | 238,315 |
| `S-Vw7.csv` | Phone CSV | 1,602 | S2 | 0 | 300,843 |
| `S-Vw8.csv` | Phone CSV | 1,529 | S2 | 0 | 287,123 |
| `S-Vw9.csv` | Phone CSV | 552 | S2 | 0 | 103,572 |
| `S-Y1.csv` | Phone CSV | 70,285 | S2 | 98 | 13,039,543 |

### `Unsynchronised V and S Dataset/Unsynchronised V and S Dataset/Uncategorised IOVNB (V and S) Dataset/V-Dataset`

| File | Kind | Rows / dimensions / archived files | Schema | Missing cells | Bytes |
| --- | --- | ---: | --- | ---: | ---: |
| `V-M.csv` | Vehicle CSV | 105,995 | S1 | 0 | 21,659,868 |
| `V-S1.csv` | Vehicle CSV | 51,790 | S1 | 0 | 10,505,959 |
| `V-S2.csv` | Vehicle CSV | 93,900 | S1 | 0 | 19,297,256 |
| `V-S3a.csv` | Vehicle CSV | 24,660 | S1 | 0 | 5,089,354 |
| `V-S3b.csv` | Vehicle CSV | 6,840 | S1 | 0 | 1,410,120 |
| `V-S3c.csv` | Vehicle CSV | 37,220 | S1 | 0 | 7,687,239 |
| `V-S4.csv` | Vehicle CSV | 97,824 | S1 | 0 | 19,863,006 |
| `V-St1.csv` | Vehicle CSV | 57,213 | S1 | 0 | 11,545,416 |
| `V-St4.csv` | Vehicle CSV | 13,591 | S1 | 0 | 2,794,203 |
| `V-St6.csv` | Vehicle CSV | 51,360 | S1 | 0 | 10,437,990 |
| `V-St7.csv` | Vehicle CSV | 44,427 | S1 | 0 | 8,944,996 |
| `V-Vfa01.csv` | Vehicle CSV | 11,535 | S1 | 0 | 2,398,099 |
| `V-Vfa02.csv` | Vehicle CSV | 67,755 | S1 | 0 | 13,955,001 |
| `V-Vfb01a.csv` | Vehicle CSV | 17,000 | S1 | 0 | 3,363,089 |
| `V-Vfb01b.csv` | Vehicle CSV | 3,880 | S1 | 0 | 795,266 |
| `V-Vfb01c.csv` | Vehicle CSV | 6,320 | S1 | 0 | 1,280,169 |
| `V-Vfb01d.csv` | Vehicle CSV | 10,713 | S1 | 0 | 2,123,447 |
| `V-Vfb02a.csv` | Vehicle CSV | 35,960 | S1 | 0 | 7,418,599 |
| `V-Vfb02b.csv` | Vehicle CSV | 11,000 | S1 | 0 | 2,240,834 |
| `V-Vfb02c.csv` | Vehicle CSV | 640 | S1 | 0 | 132,991 |
| `V-Vfb02d.csv` | Vehicle CSV | 880 | S1 | 0 | 182,339 |
| `V-Vfb02e.csv` | Vehicle CSV | 980 | S1 | 0 | 202,703 |
| `V-Vfb02f.csv` | Vehicle CSV | 660 | S1 | 0 | 136,684 |
| `V-Vfb02g.csv` | Vehicle CSV | 27,159 | S1 | 0 | 5,570,770 |
| `V-Vta10.csv` | Vehicle CSV | 1,570 | S1 | 0 | 321,356 |
| `V-Vta11.csv` | Vehicle CSV | 589 | S1 | 0 | 122,161 |
| `V-Vta12.csv` | Vehicle CSV | 690 | S1 | 0 | 140,652 |
| `V-Vta13.csv` | Vehicle CSV | 473 | S1 | 0 | 98,450 |
| `V-Vta14.csv` | Vehicle CSV | 2,893 | S1 | 0 | 593,318 |
| `V-Vta15.csv` | Vehicle CSV | 869 | S1 | 0 | 177,465 |
| `V-Vta16.csv` | Vehicle CSV | 11,361 | S1 | 0 | 2,312,817 |
| `V-Vta17.csv` | Vehicle CSV | 4,594 | S1 | 0 | 944,997 |
| `V-Vta18.csv` | Vehicle CSV | 100 | S1 | 0 | 21,300 |
| `V-Vta19.csv` | Vehicle CSV | 310 | S1 | 0 | 62,292 |
| `V-Vta1a.csv` | Vehicle CSV | 25,821 | S1 | 0 | 5,288,733 |
| `V-Vta1b.csv` | Vehicle CSV | 956 | S1 | 0 | 198,110 |
| `V-Vta2.csv` | Vehicle CSV | 10,995 | S1 | 0 | 2,222,734 |
| `V-Vta20.csv` | Vehicle CSV | 3,223 | S1 | 0 | 577,317 |
| `V-Vta21.csv` | Vehicle CSV | 2,088 | S1 | 0 | 430,922 |
| `V-Vta22.csv` | Vehicle CSV | 1,572 | S1 | 0 | 323,518 |
| `V-Vta23.csv` | Vehicle CSV | 1,119 | S1 | 0 | 232,810 |
| `V-Vta24.csv` | Vehicle CSV | 1,184 | S1 | 0 | 241,654 |
| `V-Vta25.csv` | Vehicle CSV | 646 | S1 | 0 | 129,385 |
| `V-Vta26.csv` | Vehicle CSV | 1,947 | S1 | 0 | 388,954 |
| `V-Vta27.csv` | Vehicle CSV | 2,853 | S1 | 0 | 583,915 |
| `V-Vta28.csv` | Vehicle CSV | 4,219 | S1 | 0 | 859,662 |
| `V-Vta29.csv` | Vehicle CSV | 23,737 | S1 | 0 | 4,907,770 |
| `V-Vta3.csv` | Vehicle CSV | 875 | S1 | 0 | 175,163 |
| `V-Vta30.csv` | Vehicle CSV | 17,179 | S1 | 0 | 3,460,420 |
| `V-Vta4.csv` | Vehicle CSV | 1,809 | S1 | 0 | 370,003 |
| `V-Vta5.csv` | Vehicle CSV | 357 | S1 | 0 | 73,728 |
| `V-Vta6.csv` | Vehicle CSV | 1,393 | S1 | 0 | 284,633 |
| `V-Vta7.csv` | Vehicle CSV | 857 | S1 | 0 | 176,565 |
| `V-Vta8.csv` | Vehicle CSV | 3,697 | S1 | 0 | 732,865 |
| `V-Vta9.csv` | Vehicle CSV | 226 | S1 | 0 | 46,738 |
| `V-Vtb1.csv` | Vehicle CSV | 32,459 | S1 | 0 | 6,696,680 |
| `V-Vtb10.csv` | Vehicle CSV | 195 | S1 | 0 | 40,687 |
| `V-Vtb11.csv` | Vehicle CSV | 433 | S1 | 0 | 88,068 |
| `V-Vtb12.csv` | Vehicle CSV | 490 | S1 | 0 | 98,988 |
| `V-Vtb13.csv` | Vehicle CSV | 1,245 | S1 | 0 | 256,729 |
| `V-Vtb2.csv` | Vehicle CSV | 5,712 | S1 | 0 | 1,149,458 |
| `V-Vtb3.csv` | Vehicle CSV | 8,289 | S1 | 0 | 1,663,807 |
| `V-Vtb4.csv` | Vehicle CSV | 625 | S1 | 0 | 127,079 |
| `V-Vtb5.csv` | Vehicle CSV | 64,610 | S1 | 0 | 13,070,303 |
| `V-Vtb6.csv` | Vehicle CSV | 508 | S1 | 0 | 104,997 |
| `V-Vtb7.csv` | Vehicle CSV | 461 | S1 | 0 | 94,550 |
| `V-Vtb8.csv` | Vehicle CSV | 699 | S1 | 0 | 138,144 |
| `V-Vtb9.csv` | Vehicle CSV | 457 | S1 | 0 | 92,473 |
| `V-Vw1.csv` | Vehicle CSV | 20,475 | S1 | 0 | 3,923,291 |
| `V-Vw10.csv` | Vehicle CSV | 670 | S1 | 0 | 138,464 |
| `V-Vw11.csv` | Vehicle CSV | 4,924 | S1 | 0 | 997,043 |
| `V-Vw12.csv` | Vehicle CSV | 1,069 | S1 | 0 | 212,441 |
| `V-Vw13.csv` | Vehicle CSV | 297 | S1 | 0 | 58,854 |
| `V-Vw14a.csv` | Vehicle CSV | 3,140 | S1 | 0 | 627,655 |
| `V-Vw14b.csv` | Vehicle CSV | 19,600 | S1 | 0 | 3,987,718 |
| `V-Vw14c.csv` | Vehicle CSV | 15,857 | S1 | 0 | 3,237,111 |
| `V-Vw15.csv` | Vehicle CSV | 1,391 | S1 | 0 | 253,875 |
| `V-Vw16a.csv` | Vehicle CSV | 6,000 | S1 | 0 | 1,209,828 |
| `V-Vw16b.csv` | Vehicle CSV | 1,171 | S1 | 0 | 236,875 |
| `V-Vw17.csv` | Vehicle CSV | 329 | S1 | 0 | 68,566 |
| `V-Vw2.csv` | Vehicle CSV | 52,712 | S1 | 0 | 10,887,065 |
| `V-Vw3.csv` | Vehicle CSV | 3,941 | S1 | 0 | 821,795 |
| `V-Vw4.csv` | Vehicle CSV | 126,573 | S1 | 0 | 26,069,987 |
| `V-Vw5.csv` | Vehicle CSV | 1,050 | S1 | 0 | 215,664 |
| `V-Vw6.csv` | Vehicle CSV | 1,288 | S1 | 0 | 269,988 |
| `V-Vw7.csv` | Vehicle CSV | 1,689 | S1 | 0 | 350,184 |
| `V-Vw8.csv` | Vehicle CSV | 1,599 | S1 | 0 | 332,898 |
| `V-Vw9.csv` | Vehicle CSV | 601 | S1 | 0 | 125,970 |
| `V-Y1.csv` | Vehicle CSV | 70,341 | S1 | 0 | 14,394,860 |
| `V-Y2.csv` | Vehicle CSV | 57,213 | S1 | 0 | 11,546,741 |

## Sources and interpretation notes

- Local CSV/JPG/ZIP payloads: exact headers, row counts, field completeness, simple type/range profiles, image dimensions, archive entries, and SHA-256 duplicate detection.
- [README_1.pdf](README_1.pdf): study design, sensor descriptions, driver styles, scenarios, and published run metadata. The PDF has several header/label inconsistencies with the data; this catalog gives precedence to the files for exact schemas.
- [README.md](README.md): repository overview and aggregate study claims.
- The local `Data Checker Table 2.py` is a processing script in the unsynchronized categorized vehicle tree, not a CSV dataset; it is not included in the 727 CSV/JPG/ZIP inventory entries.
