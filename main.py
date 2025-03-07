from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.types import TxOpts, TokenAccountOpts
from spl.token.instructions import close_account, CloseAccountParams, BurnParams, burn
from spl.token.constants import TOKEN_PROGRAM_ID
import base58
import time
import getpass


class SolanaClient:
    """Handles Solana RPC connections and operations"""
    
    RPC_ENDPOINTS = {
        "solana-mainnet": "https://api.mainnet-beta.solana.com",
        "publicnode": "https://solana-rpc.publicnode.com",
        "helius": None,  # require api key
        "quicknode": None,  # require custom url
        "custom": None  # will use custom_config directly
    }
    
    def __init__(self, endpoint_key="solana-mainnet", custom_config=None):
        if endpoint_key == "custom":
            self.endpoint = custom_config
        elif custom_config and endpoint_key in ["helius", "quicknode"]:
            if endpoint_key == "helius":
                self.endpoint = f"https://mainnet.helius-rpc.com/?api-key={custom_config}"
            else:
                self.endpoint = custom_config
        else:
            self.endpoint = self.RPC_ENDPOINTS.get(endpoint_key, self.RPC_ENDPOINTS["solana-mainnet"])
        
        self.client = Client(self.endpoint)
    
    def get_token_accounts(self, owner):
        """Get all token accounts owned by the specified wallet"""
        response = self.client.get_token_accounts_by_owner(
            owner=owner,
            opts=TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)
        )
        return response.value
    
    def get_token_account_info(self, token_pubkey):
        """Get detailed information about a token account"""
        response = self.client.get_account_info_json_parsed(pubkey=token_pubkey)
        return response.value.data.parsed['info']
    
    def get_token_balance(self, token_pubkey):
        """Get token balance for an account"""
        response = self.client.get_token_account_balance(pubkey=token_pubkey)
        return response.value.amount
    
    def get_sol_balance(self, pubkey):
        """Get SOL balance for an account"""
        return self.client.get_balance(pubkey).value


class Wallet:
    """Represents a Solana wallet"""
    
    def __init__(self, private_key_base58):
        private_key_bytes = base58.b58decode(private_key_base58)
        self.keypair = Keypair.from_bytes(private_key_bytes)
    
    @property
    def pubkey(self):
        return self.keypair.pubkey()


class TokenAccount:
    """Represents a token account with its operations"""
    
    def __init__(self, pubkey, client, wallet, index=0):
        self.pubkey = pubkey
        self.client = client
        self.wallet = wallet
        self.index = index
        self.load_data()
    
    def load_data(self):
        """Load token account data from blockchain"""
        self.token_balance = self.client.get_token_balance(self.pubkey)
        account_info = self.client.get_token_account_info(self.pubkey)
        self.mint_address = account_info['mint']
        self.mint_pubkey = Pubkey.from_string(self.mint_address)
        self.sol_balance = self.client.get_sol_balance(self.pubkey)
        self.acc_info_test = account_info
    
    def create_burn_instruction(self):
        """Create instruction to burn tokens"""
        return burn(BurnParams(
            program_id=TOKEN_PROGRAM_ID,
            account=self.pubkey,
            mint=self.mint_pubkey,
            owner=self.wallet.pubkey,
            amount=int(self.token_balance)
        ))
    
    def create_close_instruction(self):
        """Create instruction to close the token account"""
        return close_account(CloseAccountParams(
            account=self.pubkey,
            dest=self.wallet.pubkey,
            owner=self.wallet.pubkey,
            program_id=TOKEN_PROGRAM_ID
        ))
    
    def display_info(self):
        """Display token account information"""
        print(f"Token number [{self.index}]")
        print(f"Account: https://solscan.io/account/{self.pubkey}")
        print(f"Token address: https://solscan.io/token/{self.mint_pubkey}")
        print(f"Balance: {self.token_balance}")


class TokenBurner:
    """Main class to burn tokens and close accounts"""
    
    def __init__(self, private_key, rpc_endpoint="solana-mainnet", custom_config=None):
        self.client = SolanaClient(rpc_endpoint, custom_config)
        self.wallet = Wallet(private_key)
    
    def get_all_token_accounts(self):
        """Get all token accounts owned by the wallet"""
        accounts_data = self.client.get_token_accounts(self.wallet.pubkey)
        token_accounts = []
        for i, account_data in enumerate(accounts_data):
            token_accounts.append(TokenAccount(account_data.pubkey, self.client, self.wallet, i+1))
        return token_accounts
    
    def process_token_account(self, token_account, force_burn=False):
        """Process a single token account - burn tokens if needed and close it"""
        token_account.display_info()
        
        instructions = []
        
        if int(token_account.token_balance) > 0:
            if force_burn:
                print(f"Burning {token_account.token_balance} tokens")
                instructions.append(token_account.create_burn_instruction())
            else:
                print(f"Token balance not ZERO, skipping\n")
                return False
        
        instructions.append(token_account.create_close_instruction())
        
        recent_blockhash = self.client.client.get_latest_blockhash().value.blockhash
        transaction = Transaction.new_signed_with_payer(
            instructions=instructions,
            payer=self.wallet.pubkey,
            signing_keypairs=[self.wallet.keypair],
            recent_blockhash=recent_blockhash
        )
        
        response = self.client.client.send_transaction(
            transaction,
            opts=TxOpts(skip_preflight=True)
        )
        
        print(f"Transaction sent: https://solscan.io/tx/{str(response.value)}")
        print(f"Transferred {token_account.sol_balance / 1_000_000_000} SOL\n")
        return True
    
    def burn_all_tokens(self):
        """Process all token accounts"""
        token_accounts = self.get_all_token_accounts()
        print(f"Found {len(token_accounts)} token accounts\n")
        
        non_zero_tokens = []
        for token_account in token_accounts:
            token_account.display_info()
            print()
            if int(token_account.token_balance) > 0:
                non_zero_tokens.append(token_account)
        
        success_count = 0
        if non_zero_tokens:
            print("\n=== Non-Zero Balance Tokens ===")
            for token in non_zero_tokens:
                print(f"Token [{token.index}]: Balance = {token.token_balance}")
            
            burn_input = input("\nEnter token numbers to burn (space-separated) or press Enter to skip: ")
            tokens_to_burn = []
            
            if burn_input.strip():
                try:
                    burn_indices = [int(idx) for idx in burn_input.split()]
                    tokens_to_burn = [t for t in token_accounts if t.index in burn_indices]
                except ValueError:
                    print("Invalid input. Using only zero-balance tokens.")
            
            for token in tokens_to_burn:
                self.process_token_account(token, force_burn=True)
                success_count += 1
                time.sleep(1)
        
        for token_account in token_accounts:
            if int(token_account.token_balance) == 0:
                if self.process_token_account(token_account):
                    success_count += 1
                    time.sleep(1)
        
        print(f"Successfully processed {success_count} out of {len(token_accounts)} accounts")


def get_private_key():
    """Prompt user for private key input"""
    print("\n=== Solana Token Burner ===")
    print("It automatically close empty token accounts and asks on which non-empty token accounts to burn the token and close the account")
    print("Please enter your private key (input is hidden for security):")
    return getpass.getpass("Private key: ")


def select_rpc_endpoint():
    """Allow user to select RPC endpoint with custom configuration if needed"""
    print("\n=== RPC Endpoint Selection ===")
    print("Available RPC endpoints:")
    print("1. Solana Mainnet (api.mainnet-beta.solana.com), default option")
    print("2. Public Node (solana-rpc.publicnode.com), recommended")
    print("3. Helius (requires API key)")
    print("4. QuickNode (requires custom URL)")
    print("5. Custom RPC endpoint")
    
    choice = input("\nSelect RPC endpoint (1-5): ")
    
    endpoint_map = {
        "1": "solana-mainnet",
        "2": "publicnode",
        "3": "helius",
        "4": "quicknode",
        "5": "custom"
    }
    
    endpoint_key = endpoint_map.get(choice, "solana-mainnet")
    custom_config = None
    
    if endpoint_key == "helius":
        custom_config = input("Enter your Helius API key: ")
        print(f"Using Helius RPC with provided API key")
    elif endpoint_key == "quicknode":
        custom_config = input("Enter your QuickNode RPC URL: ")
        print(f"Using custom QuickNode RPC URL")
    elif endpoint_key == "custom":
        custom_url = input("Enter custom RPC URL: ")
        endpoint_key = "custom"
        custom_config = custom_url
        print(f"Using custom RPC endpoint: {custom_url}")
    else:
        print(f"Using {endpoint_key} RPC endpoint")
    
    return endpoint_key, custom_config


def main():
    private_key = get_private_key()
    endpoint_key, custom_config = select_rpc_endpoint()
    burner = TokenBurner(private_key, endpoint_key, custom_config)
    
    print("\nStarting token account processing...")
    burner.burn_all_tokens()


if __name__ == "__main__":
    main()