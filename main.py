import sys
from config import global_config
from Seckill import Seckiller
from WaitingAndBuy import Waiter

if __name__ == '__main__':
    choiceList = """  
===== 注意 =====
使用前请按要求填写config.ini中的
                                        
功能列表：                                                                                
 1.预约商品
 2.秒杀抢购商品
 3.缺货上架自动加购物车下单
    """
    print(choiceList)
    choice_function = global_config.getRaw("config", "model")
    if choice_function == '':
        choice_function = input('请选择:')
    global_config.setModel(choice_function)
    if choice_function == '1':
        jd_seckill = Seckiller()
        jd_seckill.reserve()
    elif choice_function == '2':
        jd_seckill = Seckiller()
        jd_seckill.seckill_by_proc_pool()
    elif choice_function == '3':
        waiter = Waiter()
        waiter.waitForSell()
    else:
        print('没有此功能')
        sys.exit(1)

