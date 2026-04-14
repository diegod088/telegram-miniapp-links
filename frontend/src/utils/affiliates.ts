export const isAffiliateDomain = (url: string): boolean => {
  try {
    const domain = new URL(url).hostname.toLowerCase();
    
    // Lista de dominios que coinciden
    const affiliateDomains = [
      'terabox.com',
      'teraboxapp.com',
      'sophon.com',
      'sophon.io',
      'cash.app',
      'cash.me',
      'snap.com',
      'snapchat.com'
    ];

    // Verificar coincidencias exactas y comodines (amazon.*, aliexpress.*)
    return affiliateDomains.includes(domain) || 
           domain.includes('amazon.') || 
           domain.includes('aliexpress.');
           
  } catch (e) {
    return false; // URL inválida
  }
};
