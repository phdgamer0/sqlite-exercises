-- A badly designed single table (like the first SAMULAS draft in Hafta 3).
-- Used by exercise 06.08:  .read data/flat_rides.sql
DROP TABLE IF EXISTS flat_rides;
CREATE TABLE flat_rides (
    rider    TEXT,
    station  TEXT,
    district TEXT,
    rode_at  TEXT
);
INSERT INTO flat_rides VALUES
  ('Ayse Yilmaz',  'Gar',           'Ilkadim',  '2026-10-01 08:05'),
  ('Ayse Yilmaz',  'Universite',    'Atakum',   '2026-10-01 17:40'),
  ('Mehmet Kaya',  'Gar',           'Ilkadim',  '2026-10-01 08:20'),
  ('Mehmet Kaya',  'Saathane',      'Ilkadim',  '2026-10-02 09:10'),
  ('Ayse Yilmaz',  'Gar',           'Ilkadim',  '2026-10-02 08:01'),
  ('Selin Aydin',  'OMU Rektorluk', 'Atakum',   '2026-10-02 07:55'),
  ('Selin Aydin',  'Universite',    'Atakum',   '2026-10-02 16:30'),
  ('Selin Aydin',  'Gar',           'Ilkadim',  '2026-10-03 10:15'),
  ('Can Demir',    'Tekkekoy',      'Tekkekoy', '2026-10-03 07:30'),
  ('Ayse Yilmaz',  'Universite',    'Atakum',   '2026-10-03 17:45'),
  ('Mehmet Kaya',  'Gar',           'Ilkadim',  '2026-10-04 08:25'),
  ('Can Demir',    'Saathane',      'Ilkadim',  '2026-10-04 12:00');
