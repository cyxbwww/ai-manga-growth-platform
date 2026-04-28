export interface DictionaryOption {
  label: string
  value: string
}

export interface DictionaryResponse {
  markets: DictionaryOption[]
  languages: DictionaryOption[]
  genres: DictionaryOption[]
  project_stages: DictionaryOption[]
  project_statuses: DictionaryOption[]
  priorities: DictionaryOption[]
}
