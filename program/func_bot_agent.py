from func_private import place_market_order,check_order_status
from datetime import datetime, timedelta
from func_public import get_contract_cn_name
import time

from pprint import pprint


# class: agent for managing opening and closing trades

class BotAgent:
    # initialize
    def __init__(
        self,
        market_1,
        market_2,
        base_side,
        base_size,
        base_price,
        quote_side,
        quote_size,
        quote_price,
        accept_failsafe_base_price,
        z_score,
        half_life,
        hedge_ratio,
        ):
        self.market_1 = market_1
        self.market_2 = market_2
        self.base_side = base_side
        self.base_size = base_size
        self.base_price = base_price
        self.quote_side = quote_side
        self.quote_size = quote_size
        self.quote_price = quote_price
        self.accept_failsafe_base_price = accept_failsafe_base_price
        self.z_score = z_score
        self.half_life = half_life
        self.hedge_ratio = hedge_ratio

        # initialize output variable
        # pair status options are failed ,live, close ,error
        self.order_dict = {
            "market_1": market_1,
            "market_2": market_2,
            "market_1_cn": get_contract_cn_name(market_1),
            "market_2_cn": get_contract_cn_name(market_2),
            "hedge_ratio": hedge_ratio,
            "z_score": z_score,
            "half_life": half_life,
            "order_id_m1": "",
            "order_m1_size": base_size,
            "order_m1_side": base_side,
            "order_time_m1": "",
            "order_id_m2": "",
            "order_m2_size": quote_size,
            "order_m2_side": quote_side,
            "order_time_m2": "",
            "pair_status": "",
            "comments": "",            
        }

    def check_order_status_by_id(self,id):
        return 'live'
    
    #open trade
    def open_trades(self):
        # print status
        print('---')
        print(f"{get_contract_cn_name(self.market_1)}: Placing first order...")
        print(f"Side: {self.base_side}, Size: {self.base_size}, Price: {self.base_price}")
        print('---')
        
        # place base order
        try:
            base_order = place_market_order(
                market=self.market_1,
                side=self.base_side,
                size=self.base_size,
                price=self.base_price,
                # false for opening the order
                reduce_only=False
            )
            # store the order id
            self.order_dict["order_id_m1"] = ""
            self.order_dict["order_time_m1"] = datetime.now().isoformat()
        except Exception as e:
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"Market 1 {self.market_1}: , {e}"
            return self.order_dict
        
        # ensure order is live before processing
        order_status_1 = self.check_order_status_by_id(self.order_dict["order_id_m1"])
        
        # abort if the order failed
        if order_status_1 != "live":
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"Market 1 {self.market_1} failed to fill"
            return self.order_dict            
        
        # print status
        print('---')
        print(f"{get_contract_cn_name(self.market_2)}: Placing second order...")
        print(f"Side: {self.quote_side}, Size: {self.quote_size}, Price: {self.quote_price}")
        print('---')
        
        # place quote order
        try:
            quote_order = place_market_order(
                market=self.market_2,
                side=self.quote_side,
                size=self.quote_size,
                price=self.quote_price,
                # false for opening the order
                reduce_only=False
            )
            # store the order id
            self.order_dict["order_id_m2"] = ""
            self.order_dict["order_time_m2"] = datetime.now().isoformat()
        except Exception as e:
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"Market 2 {self.market_2}: , {e}"
            return self.order_dict
        
        # ensure order is live before processing
        order_status_2 = self.check_order_status_by_id(self.order_dict["order_id_m2"])
        
        # abort if the order failed
        if order_status_2 != "live":
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"Market 2 {self.market_2} failed to fill"
            
            
            # close order 1
            try:
                close_order = place_market_order(
                    self.client,
                    market=self.market_1,
                    # quote side is alway opposite
                    side = self.quote_side,
                    size = self.base_size,
                    price = self.accept_failsafe_base_price,
                    reduce_only= True
                )
                # ensure order is live before proceeding
                time.sleep(2)
                order_status_close_order = check_order_status(self.client,close_order["order"]["id"])
                if order_status_close_order != "FILLED" :
                    print("ABORT PROGRAM")
                    print("Unexpected Error")
                    print(order_status_close_order)
                    
                    exit(1)
                
            except Exception as e:
                self.order_dict["pair_status"] = "ERROR"
                self.order_dict["comments"] = f"Close Market 1 {self.market_1}: {e}"
                print("ABORT PROGRAM")
                print("Unexpected Error")
                print(order_status_close_order)
                exit(1)
            return self.order_dict
        # return success result
        else:
            self.order_dict["pair_status"] = "LIVE"
            return self.order_dict