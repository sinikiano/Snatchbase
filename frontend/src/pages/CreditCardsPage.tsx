import React, { useEffect, useState } from 'react'
import { fetchCreditCards, CreditCard, SearchResponse } from '../services/api'
import CreditCardList from '../components/CreditCardList'
import CreditCardStats from '../components/CreditCardStats'
import Pagination from '../components/Pagination'

const CreditCardsPage: React.FC = () => {
  const [cards, setCards] = useState<CreditCard[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCards, setTotalCards] = useState(0)
  const [selectedBrand, setSelectedBrand] = useState<string>('')
  const [showStats, setShowStats] = useState(false)

  const itemsPerPage = 20

  useEffect(() => {
    loadCreditCards()
  }, [currentPage, selectedBrand])

  const loadCreditCards = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const params: {
        limit: number
        offset: number
        card_brand?: string
      } = {
        limit: itemsPerPage,
        offset: (currentPage - 1) * itemsPerPage,
      }

      if (selectedBrand) {
        params.card_brand = selectedBrand
      }

      const response: SearchResponse<CreditCard> = await fetchCreditCards(params)
      setCards(response.results)
      setTotalCards(response.total)
    } catch (err) {
      setError('Failed to load credit cards')
      console.error('Error loading credit cards:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const totalPages = Math.ceil(totalCards / itemsPerPage)

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleBrandFilter = (brand: string) => {
    setSelectedBrand(brand === selectedBrand ? '' : brand)
    setCurrentPage(1)
  }

  const cardBrands = ['Visa', 'Mastercard', 'American Express', 'Discover', 'JCB', 'Diners Club']

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">💳 Credit Cards</h1>
              <p className="mt-1 text-sm text-gray-600">
                Browse and analyze discovered credit card information
              </p>
            </div>
            <button
              onClick={() => setShowStats(!showStats)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              {showStats ? 'Show Cards' : 'Show Statistics'}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {showStats ? (
          <CreditCardStats />
        ) : (
          <>
            {/* Filters */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Filter by Brand</h2>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleBrandFilter('')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedBrand === ''
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All Brands
                </button>
                {cardBrands.map((brand) => (
                  <button
                    key={brand}
                    onClick={() => handleBrandFilter(brand)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      selectedBrand === brand
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {brand}
                  </button>
                ))}
              </div>
            </div>

            {/* Results Summary */}
            {!isLoading && (
              <div className="mb-6">
                <p className="text-sm text-gray-600">
                  Showing {cards.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0} -{' '}
                  {Math.min(currentPage * itemsPerPage, totalCards)} of {totalCards.toLocaleString()} credit cards
                  {selectedBrand && ` (filtered by ${selectedBrand})`}
                </p>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
                {error}
              </div>
            )}

            {/* Credit Cards List */}
            <CreditCardList cards={cards} isLoading={isLoading} />

            {/* Pagination */}
            {!isLoading && totalPages > 1 && (
              <div className="mt-8">
                <Pagination
                  currentPage={currentPage}
                  totalResults={totalCards}
                  resultsPerPage={itemsPerPage}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default CreditCardsPage
