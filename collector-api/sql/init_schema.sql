CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public."USER" (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  username character varying NOT NULL UNIQUE,
  password character varying NOT NULL,
  role character varying NOT NULL,
  CONSTRAINT "USER_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."LOCATIONS" (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  latitude double precision NOT NULL,
  longitude double precision NOT NULL,
  weather text,
  CONSTRAINT "LOCATIONS_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."DEVICES" (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  id_user uuid NOT NULL,
  model character varying,
  os_version character varying,
  CONSTRAINT "DEVICES_pkey" PRIMARY KEY (id),
  CONSTRAINT "DEVICES_id_user_fkey" FOREIGN KEY (id_user) REFERENCES public."USER"(id)
);

CREATE TABLE IF NOT EXISTS public."AUDIOS" (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  id_device uuid NOT NULL,
  audio_file bytea NOT NULL,
  audio_category character varying,
  decibels double precision,
  duration double precision,
  avg_frecuency double precision,
  file_extension character varying NOT NULL,
  location uuid,
  CONSTRAINT "AUDIOS_pkey" PRIMARY KEY (id),
  CONSTRAINT "AUDIOS_id_device_fkey" FOREIGN KEY (id_device) REFERENCES public."DEVICES"(id),
  CONSTRAINT "AUDIOS_location_fkey" FOREIGN KEY (location) REFERENCES public."LOCATIONS"(id)
);

CREATE TABLE IF NOT EXISTS public."BIRDS" (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  audio_id uuid NOT NULL,
  name character varying NOT NULL,
  CONSTRAINT "BIRDS_pkey" PRIMARY KEY (id),
  CONSTRAINT "BIRDS_audio_id_fkey" FOREIGN KEY (audio_id) REFERENCES public."AUDIOS"(id)
);

CREATE TABLE IF NOT EXISTS public."LOGIN" (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  token character varying NOT NULL,
  created_at timestamp with time zone NOT NULL,
  updated_at timestamp with time zone,
  time character varying,
  id_user uuid NOT NULL,
  CONSTRAINT "LOGIN_pkey" PRIMARY KEY (id),
  CONSTRAINT "LOGIN_id_user_fkey" FOREIGN KEY (id_user) REFERENCES public."USER"(id)
);

CREATE TABLE IF NOT EXISTS public.log_sample (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  timestamp timestamp with time zone NOT NULL DEFAULT now(),
  id_audio uuid,
  id_user uuid,
  id_device uuid,
  track smallint,
  payload text,
  error text,
  CONSTRAINT log_sample_pkey PRIMARY KEY (id),
  CONSTRAINT log_sample_id_audio_fkey FOREIGN KEY (id_audio) REFERENCES public."AUDIOS"(id),
  CONSTRAINT log_sample_id_device_fkey FOREIGN KEY (id_device) REFERENCES public."DEVICES"(id),
  CONSTRAINT log_sample_id_user_fkey FOREIGN KEY (id_user) REFERENCES public."USER"(id)
);
