# -*- coding: utf-8 -*-
import geatpy as ea # 导入geatpy库
from sys import path as paths
from os import path
paths.append(path.split(path.split(path.realpath(__file__))[0])[0])

class soea_psy_SEGA_templet(ea.SoeaAlgorithm):
    
    """
soea_psy_SEGA_templet : class - Polysomy Strengthen Elitist GA templet(增强精英保留的多染色体遗传算法模板)

模板说明:
    该模板是内置算法模板soea_SEGA_templet的多染色体版本，
    因此里面的种群对象为支持混合编码的多染色体种群类PsyPopulation类的对象。

算法描述:
    本模板实现的是增强精英保留的遗传算法。算法流程如下：
    1) 根据编码规则初始化N个个体的种群。
    2) 若满足停止条件则停止，否则继续执行。
    3) 对当前种群进行统计分析，比如记录其最优个体、平均适应度等等。
    4) 独立地从当前种群中选取N个母体。
    5) 独立地对这N个母体进行交叉操作。
    6) 独立地对这N个交叉后的个体进行变异。
    7) 将父代种群和交叉变异得到的种群进行合并，得到规模为2N的种群。
    8) 从合并的种群中根据选择算法选择出N个个体，得到新一代种群。
    9) 回到第2步。
    该算法宜设置较大的交叉和变异概率，甚至可以将其设置为大于1，否则生成的新一代种群中会有越来越多的重复个体。

模板使用注意:
    本模板调用的目标函数形如：aimFunc(pop), 
    其中pop为种群类的对象，代表一个种群，
    pop对象的Phen属性（即种群染色体的表现型）等价于种群所有个体的决策变量组成的矩阵，
    该函数根据该Phen计算得到种群所有个体的目标函数值组成的矩阵，并将其赋值给pop对象的ObjV属性。
    若有约束条件，则在计算违反约束程度矩阵CV后赋值给pop对象的CV属性（详见Geatpy数据结构）。
    该函数不返回任何的返回值，求得的目标函数值保存在种群对象的ObjV属性中，
                          违反约束程度矩阵保存在种群对象的CV属性中。
    例如：population为一个种群对象，则调用aimFunc(population)即可完成目标函数值的计算，
         此时可通过population.ObjV得到求得的目标函数值，population.CV得到违反约束程度矩阵。
    若不符合上述规范，则请修改算法模板或自定义新算法模板。
    
"""
    
    def __init__(self, problem, population):
        ea.SoeaAlgorithm.__init__(self, problem, population) # 先调用父类构造方法
        if str(type(population)) != "<class 'PsyPopulation.PsyPopulation'>":
            raise RuntimeError('传入的种群对象必须为PsyPopulation类型')
        self.name = 'psy-SEGA'
        self.selFunc = 'etour' # 锦标赛选择算子
        # 由于有多个染色体，因此需要用多个重组和变异算子，于是对应有多个重组和变异概率
        self.recFuncs = []
        self.mutFuncs = []
        self.pcs = []
        self.pms = []
        for i in range(population.ChromNum):
            if population.Encodings[i] == 'P':
                self.recFuncs.append('xovpmx') # 部分匹配交叉
                self.mutFuncs.append('mutinv') # 染色体片段逆转变异
            else:
                self.recFuncs.append('xovdp')  # 两点交叉
                if population.Encodings[i] == 'BG':
                    self.mutFuncs.append('mutbin') # 二进制变异
                elif population.Encodings[i] == 'RI':
                    self.mutFuncs.append('mutbga') # breeder GA中的变异算子
                else:
                    raise RuntimeError('编码方式必须为''BG''、''RI''或''P''.')
            self.pcs.append(1) # 重组概率
            self.pms.append(1) # 整条染色体的变异概率
        
    def run(self):
        #==========================初始化配置===========================
        population = self.population
        NIND = population.sizes
        self.initialization() # 初始化算法模板的一些动态参数
        #===========================准备进化============================
        population.initChrom(NIND) # 初始化种群染色体矩阵（内含染色体解码，详见PsyPopulation类的源码）
        self.problem.aimFunc(population) # 计算种群的目标函数值
        population.FitnV = ea.scaling(self.problem.maxormins * population.ObjV, population.CV) # 计算适应度
        self.evalsNum = population.sizes # 记录评价次数
        #===========================开始进化============================
        while self.terminated(population) == False:
            # 选择
            offspring = population[ea.selecting(self.selFunc, population.FitnV, NIND)]
            # 进行进化操作，分别对各种编码的染色体进行重组和变异
            for i in range(population.ChromNum):
                offspring.Chroms[i] = ea.recombin(self.recFuncs[i], offspring.Chroms[i], self.pcs[i]) # 重组
                offspring.Chroms[i] = ea.mutate(self.mutFuncs[i], offspring.Encodings[i], offspring.Chroms[i], offspring.Fields[i], self.pms[i]) # 变异
            # 求进化后个体的目标函数值
            offspring.Phen = offspring.decoding() # 染色体解码
            self.problem.aimFunc(offspring) # 计算目标函数值
            self.evalsNum += offspring.sizes # 更新评价次数
            population = population + offspring # 父子合并
            population.FitnV = ea.scaling(self.problem.maxormins * population.ObjV, population.CV) # 计算适应度
            # 得到新一代种群
            population = population[ea.selecting('dup', population.FitnV, NIND)] # 采用基于适应度排序的直接复制选择生成新一代种群
        
        return self.finishing(population) # 调用finishing完成后续工作并返回结果
    