{{/*
Expand the name of the chart.
*/}}
{{- define "opengovpension.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "opengovpension.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "opengovpension.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "opengovpension.labels" -}}
helm.sh/chart: {{ include "opengovpension.chart" . }}
{{ include "opengovpension.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "opengovpension.selectorLabels" -}}
app.kubernetes.io/name: {{ include "opengovpension.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "opengovpension.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "opengovpension.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create a default fully qualified postgresql name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "opengovpension.postgresql.fullname" -}}
{{- printf "%s-%s" (include "opengovpension.fullname" .) "postgresql" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified redis name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "opengovpension.redis.fullname" -}}
{{- printf "%s-%s" (include "opengovpension.fullname" .) "redis" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified prometheus name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "opengovpension.prometheus.fullname" -}}
{{- printf "%s-%s" (include "opengovpension.fullname" .) "prometheus" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified grafana name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "opengovpension.grafana.fullname" -}}
{{- printf "%s-%s" (include "opengovpension.fullname" .) "grafana" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "opengovpension.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s" (include "opengovpension.postgresql.fullname" .) }}
{{- else }}
{{- required "postgresql.host is required when postgresql.enabled is false" .Values.postgresql.host }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port
*/}}
{{- define "opengovpension.postgresql.port" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "5432" }}
{{- else }}
{{- required "postgresql.port is required when postgresql.enabled is false" .Values.postgresql.port }}
{{- end }}
{{- end }}

{{/*
PostgreSQL database
*/}}
{{- define "opengovpension.postgresql.database" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s" .Values.postgresql.auth.database }}
{{- else }}
{{- required "postgresql.database is required when postgresql.enabled is false" .Values.postgresql.database }}
{{- end }}
{{- end }}

{{/*
PostgreSQL username
*/}}
{{- define "opengovpension.postgresql.username" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s" .Values.postgresql.auth.username }}
{{- else }}
{{- required "postgresql.username is required when postgresql.enabled is false" .Values.postgresql.username }}
{{- end }}
{{- end }}

{{/*
PostgreSQL password
*/}}
{{- define "opengovpension.postgresql.password" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s" .Values.postgresql.auth.password }}
{{- else }}
{{- required "postgresql.password is required when postgresql.enabled is false" .Values.postgresql.password }}
{{- end }}
{{- end }}

{{/*
Redis host
*/}}
{{- define "opengovpension.redis.host" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-master" (include "opengovpension.redis.fullname" .) }}
{{- else }}
{{- required "redis.host is required when redis.enabled is false" .Values.redis.host }}
{{- end }}
{{- end }}

{{/*
Redis port
*/}}
{{- define "opengovpension.redis.port" -}}
{{- if .Values.redis.enabled }}
{{- printf "6379" }}
{{- else }}
{{- required "redis.port is required when redis.enabled is false" .Values.redis.port }}
{{- end }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "opengovpension.database.url" -}}
{{- printf "postgresql://%s:%s@%s:%s/%s" (include "opengovpension.postgresql.username" .) (include "opengovpension.postgresql.password" .) (include "opengovpension.postgresql.host" .) (include "opengovpension.postgresql.port" .) (include "opengovpension.postgresql.database" .) }}
{{- end }}

{{/*
Redis URL
*/}}
{{- define "opengovpension.redis.url" -}}
{{- printf "redis://%s:%s/0" (include "opengovpension.redis.host" .) (include "opengovpension.redis.port" .) }}
{{- end }}

{{/*
Image registry
*/}}
{{- define "opengovpension.image.registry" -}}
{{- .Values.app.image.registry | default .Values.global.imageRegistry }}
{{- end }}

{{/*
Image repository
*/}}
{{- define "opengovpension.image.repository" -}}
{{- .Values.app.image.repository }}
{{- end }}

{{/*
Image tag
*/}}
{{- define "opengovpension.image.tag" -}}
{{- .Values.app.image.tag | default .Chart.AppVersion }}
{{- end }}

{{/*
Full image name
*/}}
{{- define "opengovpension.image" -}}
{{- printf "%s/%s:%s" (include "opengovpension.image.registry" .) (include "opengovpension.image.repository" .) (include "opengovpension.image.tag" .) }}
{{- end }}
