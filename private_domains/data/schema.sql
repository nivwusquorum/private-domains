drop table if exists domains;
create table domains (
  domain text not null primary key,
  ip text not null,
  lastping_ms integer not null
);

drop table if exists config;
create table config (
  key text not null primary key,
  value text not null
);
