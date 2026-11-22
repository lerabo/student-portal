// Середній бал з десятковою комою, як на сайті Django; без оцінок - риска.
export function formatAverage(average) {
  if (average === null) return '-'
  return average.toLocaleString('uk-UA', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
}
