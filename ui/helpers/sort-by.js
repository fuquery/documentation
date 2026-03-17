'use strict'

module.exports = (collection, field = 'name') => {
  if (!collection) return []

  let arr = []

  if (Array.isArray(collection)) {
    arr = collection.slice()
  } else if (typeof collection === 'object') {
    arr = Object.keys(collection).map(key => collection[key])
  } else {
    return []
  }

  arr.sort((a, b) => {
    const va = (a[field] || '').toString().toLowerCase()
    const vb = (b[field] || '').toString().toLowerCase()
    return va < vb ? -1 : va > vb ? 1 : 0
  })

  return arr
}