import React from 'react'
import { CreditCard } from '../services/api'

interface CreditCardListProps {
  cards: CreditCard[]
  isLoading?: boolean
}

const getCardBrandIcon = (brand?: string) => {
  if (!brand) return '💳'
  
  const icons: { [key: string]: string } = {
    'Visa': '💳',
    'Mastercard': '💳',
    'American Express': '💳',
    'Discover': '💳',
    'JCB': '💳',
    'Diners Club': '💳',
    'Unknown': '💳'
  }
  
  return icons[brand] || '💳'
}

const getCardBrandColor = (brand?: string) => {
  if (!brand) return 'bg-gray-100 text-gray-800'
  
  const colors: { [key: string]: string } = {
    'Visa': 'bg-blue-100 text-blue-800',
    'Mastercard': 'bg-orange-100 text-orange-800',
    'American Express': 'bg-green-100 text-green-800',
    'Discover': 'bg-purple-100 text-purple-800',
    'JCB': 'bg-red-100 text-red-800',
    'Diners Club': 'bg-indigo-100 text-indigo-800',
    'Unknown': 'bg-gray-100 text-gray-800'
  }
  
  return colors[brand] || 'bg-gray-100 text-gray-800'
}

const CreditCardList: React.FC<CreditCardListProps> = ({ cards, isLoading }) => {
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!cards || cards.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
        <div className="text-6xl mb-4">💳</div>
        <h3 className="text-xl font-semibold text-gray-700 mb-2">No Credit Cards Found</h3>
        <p className="text-gray-500">No credit card data is available in the system.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {cards.map((card) => (
        <div
          key={card.id}
          className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border border-gray-200"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-3xl">{getCardBrandIcon(card.card_brand)}</span>
                <div>
                  <h3 className="text-xl font-mono font-bold text-gray-900">
                    {card.card_number_masked || '****-****-****-****'}
                  </h3>
                  {card.card_brand && (
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold mt-1 ${getCardBrandColor(card.card_brand)}`}>
                      {card.card_brand}
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                {card.cardholder_name && (
                  <div>
                    <span className="text-gray-500 font-medium">Cardholder:</span>
                    <p className="text-gray-900 font-semibold">{card.cardholder_name}</p>
                  </div>
                )}
                
                {card.expiration && (
                  <div>
                    <span className="text-gray-500 font-medium">Expiration:</span>
                    <p className="text-gray-900 font-semibold font-mono">{card.expiration}</p>
                  </div>
                )}

                <div>
                  <span className="text-gray-500 font-medium">Device ID:</span>
                  <p className="text-gray-900 font-mono text-xs">{card.device_id}</p>
                </div>

                {card.source_file && (
                  <div>
                    <span className="text-gray-500 font-medium">Source:</span>
                    <p className="text-gray-900 text-xs truncate" title={card.source_file}>
                      {card.source_file.split('/').pop() || card.source_file}
                    </p>
                  </div>
                )}
              </div>

              <div className="mt-3 pt-3 border-t border-gray-200">
                <span className="text-xs text-gray-400">
                  Found: {new Date(card.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default CreditCardList
