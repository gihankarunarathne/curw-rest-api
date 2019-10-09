/* HACK: In order to store Rain Gauge ticks as a timeseries in the database */
INSERT INTO curw.variable VALUES
  (100, 'Tick');

/* HACK: In order to store weather station Pressure as a timeseries in the database */
INSERT INTO curw.variable VALUES
  (101, 'Pressure')